# Example

This directory contains a small example for how to leverage the capabilities in [`dagster-datacontract`](https://github.com/dataheim-io/dagster-datacontract) to provide context and metadata information to assets defined in Dagster.

## Prerequisites

Make sure to install the `dev`-dependencies:

```shell
uv sync --group dev
```

## Running the example

The example can be started with:

```shell
dagster dev -f example/assets.py
```

Now access the Dagster UI locally at [http://localhost:3000/](http://localhost:3000/).
