import os
import urllib.parse

from datacontract.data_contract import DataContractSpecification


def _normalize_path(path: str) -> str:
    parsed = urllib.parse.urlparse(path)

    if not parsed.scheme or parsed.scheme == "file":
        full_path = os.path.abspath(os.path.expanduser(path))
        return f"file://{full_path}"
    else:
        return path


def get_server_information(
    data_contract_specification: DataContractSpecification,
    server_name: str | None,
    asset_name: str,
) -> dict[str, str]:
    server = data_contract_specification.servers.get(server_name)
    if not server:
        return {}

    server_information = {}
    match server.type:
        case "azure":
            server_information["dagster/uri"] = server.location
        case "databricks":
            server_information["dagster/uri"] = server.host
            server_information["dagster/table_name"] = (
                f"{server.catalog}.{server.schema}.{asset_name}"
            )
        case "kafka":
            server_information["dagster/uri"] = server.host
        case "kinesis":
            server_information = {}
        case "local":
            server_information["dagster/uri"] = _normalize_path(server.path)
        case "oracle":
            server_information["dagster/uri"] = f"{server.host}:{server.port}"
        case "postgres":
            server_information["dagster/uri"] = f"{server.host}:{server.port}"
            server_information["dagster/table_name"] = (
                f"{server.database}.{server.schema}.{asset_name}"
            )
        case "pubsub":
            server_information = {}
        case "redshift":
            server_information["dagster/uri"] = server.endpoint
            server_information["dagster/table_name"] = (
                f"{server.database}.{server.schema}.{asset_name}"
            )
        case "s3":
            server_information["dagster/uri"] = server.location
        case "sftp":
            server_information["dagster/uri"] = server.location
        case "snowflake":
            server_information["dagster/table_name"] = (
                f"{server.database}.{server.schema}.{asset_name}"
            )
        case "sqlserver":
            server_information["dagster/table_name"] = (
                f"{server.database}.{server.schema}.{asset_name}"
            )
        case "trino":
            server_information["dagster/uri"] = f"{server.host}:{server.port}"
            server_information["dagster/table_name"] = (
                f"{server.catalog}.{server.schema}.{asset_name}"
            )
        case _:
            server_information = {}

    return server_information
