import json
import re
import textwrap
from datetime import timedelta
from typing import Any

import dagster as dg
from dagster import TableColumnLineage, TableSchema
from datacontract.data_contract import DataContract
from datacontract.model.run import ResultEnum
from loguru import logger


class DataContractLoader:
    def __init__(
        self,
        asset_name: str,
        data_contract: DataContract,
    ):
        self.asset_name = asset_name
        self.asset_key = dg.AssetKey(path=self.asset_name)
        self.data_contract = data_contract
        self.data_contract_specification = (
            self.data_contract.get_data_contract_specification()
        )
        self.metadata = self._load_metadata()
        self.tags = self._load_tags()
        self.description = self.load_description()
        self.owner = self._load_owner()
        self.version = self._load_version()
        self.cron_schedule = self._load_cron_schedule()

    def _load_metadata(
        self,
    ) -> dict[str, TableColumnLineage | TableSchema | Any] | None:
        fields = self.data_contract_specification.models.get(self.asset_name).fields

        columns = []
        deps_by_column = {}

        for column_name, column_field in fields.items():
            columns.append(
                dg.TableColumn(
                    name=column_name,
                    type=column_field.type,
                    description=column_field.description,
                )
            )

            lineage = json.loads(column_field.model_dump_json()).get("lineage")
            if not lineage:
                deps_by_column[column_name] = []
            else:
                lineage_entries = lineage.get("inputFields")

                deps_by_column[column_name] = [
                    dg.TableColumnDep(
                        asset_key=dg.AssetKey(lineage_entry["name"]),
                        column_name=lineage_entry["field"],
                    )
                    for lineage_entry in lineage_entries
                ]

        return {
            "dagster/column_schema": dg.TableSchema(columns=columns),
            "dagster/column_lineage": dg.TableColumnLineage(
                deps_by_column=deps_by_column
            ),
        }

    def _load_tags(self) -> dict[str, str]:
        """Safely load tags from data contract.

        More information about Dagster tags:
        https://docs.dagster.io/guides/build/assets/metadata-and-tags/tags
        """
        key_pattern = re.compile(r"^[\w.-]{1,63}$")
        val_pattern = re.compile(r"^[\w.-]{0,63}$")

        tags = {}

        for item in self.data_contract_specification.tags:
            if ":" in item:
                key, val = map(str.strip, item.split(":", 1))
            else:
                key, val = item.strip(), ""

            if key_pattern.match(key) and val_pattern.match(val):
                tags[key] = val
            else:
                logger.warning(f"Ignoring invalid tag: {item}")

        return tags

    def _load_owner(self) -> list[str] | None:
        owner = self.data_contract_specification.info.owner

        return [f"team:{owner}"] if owner else None

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
            return None

    def load_description(
        self, config: dict[str, Any] | None = None, separator: str = "\n"
    ) -> str | None:
        """Load and return a formatted description string based on the data contract specification.

        This method composes a description by pulling text from different parts
        of the data contract specification (e.g., model and info descriptions),
        joining them using the specified separator.

        Args:
            config (dict[str, Any] | None, optional): A configuration dictionary
                specifying the order in which to concatenate the description parts.
                Defaults to `{"order": ["model", "info"]}`.
            separator (str, optional): A string used to separate different parts
                of the description. Defaults to a newline character (`"\n"`).

        Returns:
            str | None: A single string combining the specified description parts
            if available, otherwise `None`.


        Example:
            >>> self.load_description()
            'Model description...\nInfo description...'
        """
        default_config = {"order": ["model", "info"]}

        configuration = default_config | (config or {})

        descriptions = {
            "model": self.data_contract_specification.models.get(
                self.asset_name
            ).description,
            "info": self.data_contract_specification.info.description,
        }

        parts = []
        for key in configuration["order"]:
            desc = descriptions.get(key).replace("\n", f"{separator}\n")
            if desc:
                parts.append(textwrap.dedent(desc))

        if parts:
            return f"{separator}\n".join(parts)

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
