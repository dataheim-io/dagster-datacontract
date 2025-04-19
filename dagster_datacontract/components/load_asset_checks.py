from collections.abc import Generator, Sequence
from pathlib import Path
from typing import Any

import dagster as dg
from datacontract.data_contract import DataContract
from datacontract.model.run import ResultEnum

from dagster_datacontract import DataContractLoader
from dagster_datacontract.utils.paths import get_absolute_path


def load_asset_check_specifications(
    asset_specs: Sequence[dg.components.ResolvedAssetSpec],
    context_path: Path | None = None,
    data_contract_path: str | None = None,
) -> Sequence[dg.AssetCheckSpec]:
    """TODO."""
    loaded_asset_check_specs = []

    for asset_spec in asset_specs:
        asset_contract_path = asset_spec.metadata.get("datacontract/path")
        data_contract_path = (
            asset_contract_path if asset_contract_path else data_contract_path
        )
        if data_contract_path is None:
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

        loaded_asset_check_specs.append(
            dg.AssetCheckSpec(
                name=f"check_{asset_name}",
                asset=asset_name,
                metadata=data_contract.metadata,
            )
        )

    return loaded_asset_check_specs


def load_asset_checks(
    asset_specs: Sequence[dg.components.ResolvedAssetSpec],
    context_path: Path | None = None,
    data_contract_path: str | None = None,
) -> dg.AssetChecksDefinition:
    """TODO."""
    asset_check_specs = load_asset_check_specifications(
        asset_specs=asset_specs,
        context_path=context_path,
        data_contract_path=data_contract_path,
    )

    @dg.multi_asset_check(specs=asset_check_specs)
    def multi_contract_checks(
        context: dg.AssetCheckExecutionContext,
    ) -> Generator[dg.AssetCheckResult | Any, Any, None]:
        """TODO."""
        for asset_check_spec in context.check_specs:
            metadata = asset_check_spec.metadata
            context.log.info(f"Metadata: {metadata}")

            contract_path: dg.UrlMetadataValue = metadata["datacontract/path"]
            context.log.info(f"Contract path: {contract_path.url}")

            data_contract_path = str(get_absolute_path(context_path, contract_path))
            context.log.info(f"data_contract_path: {data_contract_path}")

            data_contract = DataContract(
                data_contract_file=data_contract_path,
                server="production",
            )

            run = data_contract.test()
            context.log.info(f"run.result: {run.result}")
            context.log.info(
                f"run.result == ResultEnum.passed: {run.result == ResultEnum.passed}"
            )

            context.log.info(f"asset_check_spec.key: {asset_check_spec.key}")
            context.log.info(
                f"asset_check_spec.key.asset_key: {asset_check_spec.key.asset_key}"
            )
            context.log.info(
                f"asset_check_spec.key.asset_key.path: {asset_check_spec.key.asset_key.path[0]}"
            )
            yield dg.AssetCheckResult(
                asset_key=asset_check_spec.key.asset_key.path[0],
                passed=(run.result == ResultEnum.passed),
                metadata={
                    "quality check": run.pretty(),
                },
            )

    return multi_contract_checks
