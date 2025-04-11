import json
import textwrap
from datetime import timedelta
from typing import Any

import dagster as dg
from dagster import TableColumnLineage, TableSchema
from datacontract.data_contract import DataContract
from datacontract.model.run import ResultEnum


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
        self.description = self._load_description()
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
        tags = {
            item.split(":")[0].strip(): item.split(":")[1].strip()
            if ":" in item
            else ""
            for item in self.data_contract_specification.tags
        }

        return tags

    def _load_description(self) -> str | None:
        model_description = self.data_contract_specification.models.get(
            self.asset_name
        ).description.replace("\n", "\n\n")
        info_description = self.data_contract_specification.info.description.replace(
            "\n", "\n\n"
        )

        if model_description and info_description:
            return f"{model_description}\n\n{info_description}"
        elif model_description:
            return textwrap.dedent(model_description)
        elif info_description:
            return textwrap.dedent(info_description)

        return None

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

    def load_data_quality_checks(self) -> dg.AssetChecksDefinition:
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
        freshness_checks = dg.build_last_update_freshness_checks(
            assets=[self.asset_name],
            lower_bound_delta=lower_bound_delta,
            deadline_cron=self.cron_schedule,
        )

        return freshness_checks
