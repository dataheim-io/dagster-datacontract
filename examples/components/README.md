# Dagster Components with Data Contracts

This directory contains an example for how to leverage the capabilities in `dagster-datacontract` to provide context and metadata information to assets defined using Dagster Components.

## Prerequisites

Make sure to set up the example subproject:

```shell
cd examples/components
uv venv
source .venv/bin/activate
uv sync
```

## Running the example

The example can be started with:

```shell
cd examples/components
dg dev
```

Now access the Dagster UI locally at [http://localhost:3000/](http://localhost:3000/).
