# dagster-datacontract

[Dagster](https://github.com/dagster-io/dagster) [Datacontract](https://github.com/datacontract/datacontract-cli) implementation for loading asset metadata and context information from data contracts to Dagster assets.

## Installation

Install `dagster-datacontract` using [`uv`](https://github.com/astral-sh/uv):

```shell
uv add dagster-datacontract
```

## Example

The following example can be found inside the [examples](https://github.com/dataheim-io/dagster-datacontract/tree/main/examples)-directory:

```python
from datetime import timedelta
from pathlib import Path

import dagster as dg
import polars as pl
import requests
from datacontract.data_contract import DataContract

from dagster_datacontract import DataContractLoader

asset_name = "yellow_taxi_trip_records"
examples_path = Path(__file__).resolve().parent.parent
data_contract = DataContractLoader(
    asset_name=asset_name,
    data_contract=DataContract(
        data_contract_file=str(examples_path / "datacontracts" / "datacontract.yml"),
        server="production",
    ),
)


@dg.asset(
    name=asset_name,
    metadata=data_contract.metadata,
    tags=data_contract.tags,
    description=data_contract.description,
    owners=data_contract.owner,
    code_version=data_contract.version,
)
def yellow_taxi_trip_records(
    context: dg.AssetExecutionContext,
) -> None:
    download_path = examples_path.parent.parent / "data"
    Path(download_path).mkdir(parents=True, exist_ok=True)

    url = "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2025-01.parquet"
    response = requests.get(url=url)

    file_path = f"{download_path}/yellow_tripdata_2025-01.parquet"
    context.log.info(f"Reading data from '{url}' and writing to '{file_path}'.")
    with open(file_path, "wb") as f:
        f.write(response.content)

    df = pl.read_parquet(file_path)
    context.log.info(f"File contents downloaded:\n{df}")


asset_check_yellow_taxi_trip_records = data_contract.load_data_quality_checks()

freshness_checks = data_contract.load_freshness_checks(
    lower_bound_delta=timedelta(minutes=5)
)
freshness_checks_sensor = dg.build_sensor_for_freshness_checks(
    freshness_checks=freshness_checks,
    default_status=dg.DefaultSensorStatus.RUNNING,
)

job = dg.define_asset_job(
    name="monthly_taxi_trips",
    selection=[asset_name],
)
schedule = dg.ScheduleDefinition(
    job=job,
    cron_schedule=data_contract.cron_schedule,
    default_status=dg.DefaultScheduleStatus.RUNNING,
)


defs = dg.Definitions(
    assets=[yellow_taxi_trip_records],
    asset_checks=[asset_check_yellow_taxi_trip_records, *freshness_checks],
    schedules=[schedule],
    sensors=[freshness_checks_sensor],
)
```
