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

from dagster_datacontract.components import (
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

    download_path: str
    data_contract_path: str
    asset_specs: Sequence[ResolvedAssetSpec]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        resolved_download_path = Path(context.path, self.download_path).absolute()
        asset_specs = load_asset_specifications(
            asset_specs=self.asset_specs,
            context_path=context.path,
            data_contract_path=self.data_contract_path,
        )

        @dg.multi_asset(
            name="yellow_taxi_trip_records", specs=asset_specs, can_subset=True
        )
        def _asset(context: dg.AssetExecutionContext):
            selected = context.selected_asset_keys or {spec.key for spec in asset_specs}

            self.execute(context, selected, resolved_download_path)

            context.log.info(
                f"context.selected_asset_keys: {context.selected_asset_keys}"
            )

        asset_checks = load_asset_checks(
            asset_specs=self.asset_specs,
            context_path=context.path,
            data_contract_path=self.data_contract_path,
        )

        # Add definition construction logic here.
        return dg.Definitions(
            assets=[_asset],
            asset_checks=[asset_checks],
        )

    def execute(
        self,
        context: dg.AssetExecutionContext,
        selected,
        resolved_download_path: Path,
    ) -> None:
        resolved_download_path.mkdir(parents=True, exist_ok=True)

        url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet"
        response = requests.get(url=url)

        file_path = f"{resolved_download_path}/yellow_tripdata_2025-01.parquet"
        context.log.info(f"Reading data from '{url}' and writing to '{file_path}'.")
        with open(file_path, "wb") as f:
            f.write(response.content)

        df = pl.read_parquet(file_path)
        context.log.info(f"File contents downloaded:\n{df}")
