import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import dagster as dg
from dagster.components import (
    Component,
    ComponentLoadContext,
    Resolvable,
    ResolvedAssetSpec,
)

from dagster_datacontract import (
    load_asset_checks,
    load_asset_specifications,
)


@dataclass
class IngestParquetFromAPI(Component, Resolvable):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    script_path: str
    data_contract_path: str
    asset_specs: Sequence[ResolvedAssetSpec]
    asset_check_specs: Sequence[dict[str, Any]]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        resolved_script_path = Path(context.path, self.script_path).absolute()
        asset_specs = load_asset_specifications(
            context.path, self.data_contract_path, self.asset_specs
        )
        asset_checks = load_asset_checks(
            context.path, self.data_contract_path, self.asset_specs
        )

        @dg.multi_asset(name=Path(self.script_path).stem, specs=asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(resolved_script_path, context)

        """
        check_specs = [
            dg.AssetCheckSpec(
                name=d["name"],
                asset="yellow_taxi_trip_records",
            )
            for d in self.asset_check_specs
        ]

        @dg.multi_asset_check(specs=check_specs)
        def _asset_check(context: dg.AssetCheckExecutionContext):
            return dg.AssetCheckResult(
                passed=True,
            )
        """

        # Add definition construction logic here.
        return dg.Definitions(
            assets=[_asset],
            asset_checks=[asset_checks],
        )

    def execute(self, resolved_script_path: Path, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", str(resolved_script_path)], check=True)
