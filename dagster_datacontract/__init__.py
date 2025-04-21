from datetime import timedelta
from typing import Any

import dagster as dg
from datacontract.data_contract import DataContract
from datacontract.model.run import ResultEnum
from loguru import logger

from dagster_datacontract.description import get_description
from dagster_datacontract.metadata import (
    get_column_lineage,
    get_links,
    get_server_information,
    get_table_column,
)
from dagster_datacontract.owners import get_owner
from dagster_datacontract.tags import get_tags
from dagster_datacontract.utils import combine_parts, normalize_path


class DataContractLoader:
    def __init__(
        self,
        asset_name: str,
        data_contract: DataContract | None = None,
        data_contract_path: str | None = None,
    ):
        if data_contract is None and data_contract_path is None:
            raise ValueError(
                "Either 'data_contract' or 'data_contract_path' must be provided."
            )

        self.asset_name = asset_name
        self.asset_key = dg.AssetKey(path=self.asset_name)
        self.data_contract = (
            data_contract
            if data_contract
            else DataContract(data_contract_file=data_contract_path)
        )
        self.data_contract_specification = (
            self.data_contract.get_data_contract_specification()
        )
        self.metadata = self._load_metadata()
        self.tags = get_tags(self.data_contract_specification.tags)
        self.description = get_description(
            self.asset_name,
            self.data_contract_specification,
        )
        self.owner = get_owner(self.data_contract_specification)
        self.version = self._load_version()
        self.cron_schedule = self._load_cron_schedule()
        self.asset_spec = dg.AssetSpec(
            key=asset_name,
            description=self.description,
            metadata=self.metadata,
            code_version=self.version,
            owners=self.owner,
            tags=self.tags,
        )

    def _load_metadata(
        self,
    ) -> dict[str, dg.TableColumnLineage | dg.TableSchema | Any] | None:
        metadata = (
            {
                "datacontract/path": dg.MetadataValue.url(
                    normalize_path(self.data_contract._data_contract_file)
                ),
            }
            if self.data_contract._data_contract_file
            else {}
        )
        columns = []
        deps_by_column = {}

        try:
            fields = self.data_contract_specification.models.get(self.asset_name).fields

            for column_name, column_field in fields.items():
                table_column = get_table_column(column_name, column_field)
                columns.append(table_column)

                table_column_lineage = get_column_lineage(column_field)
                deps_by_column[column_name] = table_column_lineage

            metadata["dagster/column_schema"] = dg.TableSchema(columns=columns)
            metadata["dagster/column_lineage"] = dg.TableColumnLineage(
                deps_by_column=deps_by_column
            )
        except AttributeError as e:
            logger.warning(
                f"No field named {self.asset_name} found in data contract.\n{e}"
            )

        server_information = get_server_information(
            self.data_contract_specification,
            self.data_contract._server,
            self.asset_name,
        )
        metadata.update(server_information)

        links = get_links(self.data_contract_specification.links)
        metadata.update(links)

        return metadata

    def _load_version(self) -> str | None:
        version = self.data_contract_specification.info.version

        return version

    def _load_cron_schedule(self) -> str | None:
        try:
            cron_schedule = (
                self.data_contract_specification.servicelevels.frequency.cron
            )
            return cron_schedule
        except AttributeError:
            logger.warning("'servicelevels.frequency.cron' not found in Data Contract.")
            return None

    def load_data_quality_checks(self) -> dg.AssetChecksDefinition:
        """Define and return a data quality check for the specified asset.

        This method registers a data quality check using the `@dg.asset_check`
        decorator. The check runs the data contract's `test()` method and returns
        the result as a `dg.AssetCheckResult`. The result is considered "passed"
        if the test outcome matches `ResultEnum.passed`.

        The check is marked as blocking, which means failures may halt downstream
        processing in a data pipeline.

        Returns:
            dg.AssetChecksDefinition: The defined asset quality check function,
            registered with Dagster's data quality framework.
        """

        @dg.asset_check(
            asset=self.asset_key,
            blocking=True,
        )
        def check_asset():
            run = self.data_contract.test()

            return dg.AssetCheckResult(
                passed=run.result == ResultEnum.passed,
                metadata={
                    "quality check": run.pretty(),
                },
            )

        return check_asset

    def load_freshness_checks(self, lower_bound_delta: timedelta):
        """Generate and return freshness checks for the asset based on update recency.

        This method builds freshness checks using Dagster's
        `build_last_update_freshness_checks` utility. It ensures that the specified
        asset has been updated within a given time window (`lower_bound_delta`).
        A cron schedule (`self.cron_schedule`) defines when the check should run.

        Args:
            lower_bound_delta (timedelta): The minimum acceptable time difference
                between the current time and the asset's last update timestamp.
                If the asset is older than this delta, the check will fail.

        Returns:
            list[AssetCheckSpec] | AssetChecksDefinition: A freshness check definition
            that can be returned from `define_asset_checks` to register the check.


        Example:
            >>> self.load_freshness_checks(timedelta(hours=24))
            # Ensures the asset was updated in the last 24 hours.
        """
        freshness_checks = dg.build_last_update_freshness_checks(
            assets=[self.asset_name],
            lower_bound_delta=lower_bound_delta,
            deadline_cron=self.cron_schedule,
        )

        return freshness_checks

    def combine_asset_specs(
        self,
        asset_spec: dg.AssetSpec,
    ) -> dg.AssetSpec:
        """Merge the given AssetSpec with the current object's attributes to produce a new AssetSpec.

        This method combines metadata, descriptions, code versions, owners, and tags from the
        provided `asset_spec` and the current instance. Preference is generally given to the
        current instance's values where appropriate. Fields like dependencies, skippability,
        group name, automation condition, kinds, and partition definitions are taken directly
        from the input `asset_spec`.

        Args:
            asset_spec (dg.AssetSpec): The base asset specification to merge with the current one.

        Returns:
            dg.AssetSpec: A new AssetSpec instance containing the combined data.

        Notes:
            - Descriptions are joined with double newlines (`"\n\n"`).
            - Code versions are joined with an underscore (`"_"`).
            - Owners are concatenated.
            - Metadata and tags are merged with the current instance taking precedence.
        """
        description = combine_parts(
            [asset_spec.description, self.description], delimiter="\n\n"
        )
        metadata = {
            **asset_spec.metadata,
            **self.metadata,
        }
        code_version = combine_parts(
            [asset_spec.code_version, self.version], delimiter="_"
        )
        owners = list(asset_spec.owners) + self.owner
        tags = {**asset_spec.tags, **self.tags}

        return dg.AssetSpec(
            key=self.asset_name,
            deps=asset_spec.deps,
            description=description,
            metadata=metadata,
            skippable=asset_spec.skippable,
            group_name=asset_spec.group_name,
            code_version=code_version,
            automation_condition=asset_spec.automation_condition,
            owners=owners,
            tags=tags,
            kinds=asset_spec.kinds,
            partitions_def=asset_spec.partitions_def,
        )
