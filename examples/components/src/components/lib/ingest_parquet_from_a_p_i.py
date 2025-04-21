from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import dagster as dg
import polars as pl
import requests
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
    """Re-usable component for ingesting parquet from API.

    This is an example Dagster Component to showcase how to load
    context and metadata information from a data contract to
    the Dagster Component assets.

    By default, it can be loaded with specifying the
    `datacontract/path`-metadata within the asset_specs.
    """

    download_path: str
    asset_specs: Sequence[ResolvedAssetSpec]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        resolved_download_path = Path(context.path, self.download_path).absolute()

        def create_asset_fn(
            asset_name: str, asset_spec: dg.AssetSpec
        ) -> dg.AssetsDefinition:
            @dg.asset(
                name=asset_name,
                deps=asset_spec.deps,
                description=asset_spec.description,
                metadata=asset_spec.metadata,
                group_name=asset_spec.group_name,
                code_version=asset_spec.code_version,
                automation_condition=asset_spec.automation_condition,
                owners=asset_spec.owners,
                tags=asset_spec.tags,
                kinds=asset_spec.kinds,
                partitions_def=asset_spec.partitions_def,
            )
            def _asset(context: dg.AssetExecutionContext) -> None:
                self.execute(context, resolved_download_path, asset_name)

            return _asset

        asset_defs = []
        asset_check_defs = []

        for asset_spec in self.asset_specs:
            asset_name = asset_spec.key.path[0]
            data_contract_path = asset_spec.metadata.get("datacontract/path")
            data_contract_server = asset_spec.metadata.get("datacontract/server")

            if data_contract_path and data_contract_server:
                resolved_data_contract_path = str(
                    Path(context.path, data_contract_path)
                )

                data_contract_loader = DataContractLoader(
                    asset_name=asset_name,
                    data_contract=DataContract(
                        data_contract_file=resolved_data_contract_path,
                        server=data_contract_server,
                    ),
                )

                asset_spec = data_contract_loader.combine_asset_specs(asset_spec)
                asset_check_defs.append(data_contract_loader.load_data_quality_checks())

            asset_defs.append(create_asset_fn(asset_name, asset_spec))

        return dg.Definitions(
            assets=asset_defs,
            asset_checks=asset_check_defs,
        )

    def execute(
        self,
        context: dg.AssetExecutionContext,
        resolved_download_path: Path,
        asset_name: str,
    ) -> None:
        resolved_download_path.mkdir(parents=True, exist_ok=True)

        url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{asset_name}_2025-01.parquet"
        response = requests.get(url=url)

        file_path = f"{resolved_download_path}/{asset_name}_2025-01.parquet"
        context.log.info(f"Reading data from '{url}' and writing to '{file_path}'.")
        with open(file_path, "wb") as f:
            f.write(response.content)

        df = pl.read_parquet(file_path)
        context.log.info(f"File contents downloaded:\n{df}")
