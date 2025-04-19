from pathlib import Path

import dagster as dg
from datacontract.data_contract import DataContract

from dagster_datacontract import DataContractLoader
from dagster_datacontract.utils import get_absolute_path


def combine_asset_specs(
    asset_name: str,
    asset_spec: dg.AssetSpec,
    path: Path,
) -> dg.AssetSpec:
    """TODO."""
    data_contract_path = asset_spec.metadata.get("datacontract/path")
    if data_contract_path is None:
        return asset_spec

    resolved_data_contract_path = str(get_absolute_path(path, data_contract_path))

    data_contract = DataContractLoader(
        asset_name=asset_name,
        data_contract=DataContract(
            data_contract_file=resolved_data_contract_path,
        ),
    )

    asset_spec.metadata.update(data_contract.metadata)
    description = f"{asset_spec.description}\n\n{data_contract.description}"

    return dg.AssetSpec(
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
