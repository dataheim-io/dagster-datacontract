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

    description = f"{asset_spec.description}\n\n{data_contract.description}"
    metadata = {
        **asset_spec.metadata,
        **data_contract.metadata,
    }
    code_version = f"{asset_spec.code_version}_{data_contract.version}"  # TODO
    owners = list(asset_spec.owners) + data_contract.owner
    tags = {**asset_spec.tags, **data_contract.tags}

    return dg.AssetSpec(
        key=asset_name,
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
