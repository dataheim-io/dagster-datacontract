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
from dagster.components.resolved.core_models import ResolvedAssetCheckSpec

from dagster_datacontract.specifications import combine_asset_specs


@dataclass
class IngestParquetFromAPI(Component, Resolvable):
    """Re-usable component for ingesting parquet from API.

    This is an example Dagster Component to showcase how to load
    context and metadata information from a data contract to
    the Dagster Component assets.

    By default, it can be loaded with specifying the
    `datacontract/path` metadata value within the asset_specs.
    """

    download_path: str
    asset_specs: Sequence[ResolvedAssetSpec]
    checks: Sequence[ResolvedAssetCheckSpec]

    def get_check_specs(self) -> Sequence[dg.AssetCheckSpec]:
        return [check.to_dagster() for check in self.checks]

    def build_defs(self, context: ComponentLoadContext) -> dg.Definitions:
        # resolved_download_path = Path(context.path, self.download_path).absolute()

        def create_asset_fn(asset_spec: dg.AssetSpec) -> dg.AssetsDefinition:
            asset_name = asset_spec.key.path[0]
            combined_asset_spec = combine_asset_specs(
                asset_name, asset_spec, context.path
            )

            @dg.asset(
                name=asset_name,
                deps=asset_spec.deps,
                description=combined_asset_spec.description,
                metadata=combined_asset_spec.metadata,
                group_name=combined_asset_spec.group_name,
                code_version=combined_asset_spec.code_version,
                automation_condition=combined_asset_spec.automation_condition,
                owners=combined_asset_spec.owners,
                tags=combined_asset_spec.tags,
                kinds=combined_asset_spec.kinds,
                partitions_def=combined_asset_spec.partitions_def,
            )
            def _asset(context: dg.AssetExecutionContext) -> dg.MaterializeResult:
                context.log.info(f"Asset: {asset_name}")

                return dg.MaterializeResult()

            return _asset

        def create_asset_check_fn(
            check_spec,
        ):  #  AssetCheckSpecConfig) -> dg.AssetChecksDefinition:
            @dg.asset_check(
                name=check_spec.name,
                asset=check_spec.asset_key,
                additional_deps=check_spec.additional_deps,
                description=check_spec.description,
                blocking=check_spec.blocking,
                metadata=check_spec.metadata,
                automation_condition=check_spec.automation_condition,
            )
            def _check() -> dg.AssetCheckResult:
                return dg.AssetCheckResult(passed=True)

            return _check

        asset_defs = []
        for asset_spec in self.asset_specs:
            asset_defs.append(create_asset_fn(asset_spec))

        asset_check_defs = []
        for check in self.checks:
            asset_check_defs.append(create_asset_check_fn(check))

        return dg.Definitions(
            assets=asset_defs,
            asset_checks=asset_check_defs,
        )

    def execute(
        self,
        context: dg.AssetExecutionContext,
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
