import dagster as dg
import polars as pl


@dg.asset(
    deps=[
        "green_tripdata",
        "yellow_tripdata",
    ],
)
def combine_tripdata(context: dg.AssetExecutionContext):
    """Combines the ingested NYC trip data."""
    df_green_trips = pl.read_parquet(
        "./src/components/defs/ingest_nyc_taxi/data/green_tripdata_2025-01.parquet"
    )
    context.log.info(f"df green trips:\n{df_green_trips}")

    df_yellow_trips = pl.read_parquet(
        "./src/components/defs/ingest_nyc_taxi/data/yellow_tripdata_2025-01.parquet"
    )
    context.log.info(f"df yellow trips:\n{df_yellow_trips}")

    # Concatenate the DataFrames
    df_union = pl.concat([df_green_trips, df_yellow_trips], how="diagonal")

    context.log.info(f"Union schema: {df_union.schema}")
    context.log.info(f"df union:\n{df_union}")
