import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

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
    """Re-usable component for ingesting parquet from API.

    This is an example Dagster Component to showcase how to load
    context and metadata information from a data contract to
    the Dagster Component assets.

    By default, it can be loaded with specifying the
    `data_contract_path`-value or the `datacontract/path`
    metadata value within the asset_specs.
    """

    script_path: str
    data_contract_path: str
    asset_specs: Sequence[ResolvedAssetSpec]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        resolved_script_path = Path(context.path, self.script_path).absolute()
        asset_specs = load_asset_specifications(
            context.path, self.data_contract_path, self.asset_specs
        )
        asset_checks_spec = load_asset_checks(
            context.path, self.data_contract_path, self.asset_specs
        )

        @dg.multi_asset(name=Path(self.script_path).stem, specs=asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(resolved_script_path, context)

        # Add definition construction logic here.
        return dg.Definitions(
            assets=[_asset],
            asset_checks=[asset_checks_spec],
        )

    def execute(self, resolved_script_path: Path, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", str(resolved_script_path)], check=True)
