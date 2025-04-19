from collections.abc import Sequence
from pathlib import Path

import dagster as dg
from datacontract.data_contract import DataContract

from dagster_datacontract import DataContractLoader
from dagster_datacontract.utils import get_absolute_path


def load_asset_specifications(
    asset_specs: Sequence[dg.components.ResolvedAssetSpec],
    context_path: Path | None = None,
    data_contract_path: str | None = None,
) -> Sequence[dg.AssetSpec]:
    """TODO."""
    loaded_asset_specs = []

    for asset_spec in asset_specs:
        asset_contract_path = asset_spec.metadata.get("datacontract/path")
        data_contract_path = (
            asset_contract_path if asset_contract_path else data_contract_path
        )
        if data_contract_path is None:
            loaded_asset_specs.append(asset_spec)
            continue

        resolved_data_contract_path = str(
            get_absolute_path(context_path, data_contract_path)
        )

        asset_name = asset_spec.key.path[0]
        data_contract = DataContractLoader(
            asset_name=asset_name,
            data_contract=DataContract(
                data_contract_file=resolved_data_contract_path,
            ),
        )

        asset_spec.metadata.update(data_contract.metadata)
        description = f"{asset_spec.description}\n\n{data_contract.description}"

        loaded_asset_specs.append(
            dg.AssetSpec(
                key=asset_name,
                deps=asset_spec.deps,
                description=description,
                metadata=asset_spec.metadata,
                skippable=asset_spec.skippable,
                group_name=asset_spec.group_name,
                code_version=data_contract.version,
                automation_condition=asset_spec.automation_condition,
                owners=list(asset_spec.owners) + data_contract.owner,
                tags={**asset_spec.tags, **data_contract.tags},
                kinds=asset_spec.kinds,
                partitions_def=asset_spec.partitions_def,
            )
        )

    return loaded_asset_specs
