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
from datacontract.data_contract import DataContract

from dagster_datacontract import DataContractLoader


@dataclass
class IngestParquetFromAPI(Component, Resolvable):
    """COMPONENT SUMMARY HERE.

    COMPONENT DESCRIPTION HERE.
    """

    script_path: str
    data_contract_path: str
    asset_specs: Sequence[ResolvedAssetSpec]

    # added fields here will define yaml schema via Model

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        resolved_script_path = Path(context.path, self.script_path).absolute()

        loaded_asset_specs = []

        for asset_spec in self.asset_specs:
            resolved_datacontract_path = Path(
                context.path, self.data_contract_path
            ).absolute()
            path = str(resolved_datacontract_path)
            print(f"Contract path: {path}")

            data_contract = DataContractLoader(
                asset_name=asset_spec.key.path[0],
                data_contract=DataContract(
                    data_contract_file=path,
                ),
            )

            my_asset_spec = dg.AssetSpec(
                key=asset_spec.key.path[0],
                metadata=data_contract.metadata,
            )

            loaded_asset_specs.append(my_asset_spec)
            # asset_spec.metadata = data_contract.metadata

        # print(self.asset_specs)
        # for asset_spec in self.asset_specs:
        #    print(asset_spec)

        @dg.multi_asset(name=Path(self.script_path).stem, specs=loaded_asset_specs)
        def _asset(context: dg.AssetExecutionContext):
            self.execute(resolved_script_path, context)

        # Add definition construction logic here.
        return dg.Definitions(assets=[_asset])

    def execute(self, resolved_script_path: Path, context: dg.AssetExecutionContext):
        return subprocess.run(["sh", str(resolved_script_path)], check=True)
