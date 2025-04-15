from datacontract.data_contract import DataContractSpecification

from dagster_datacontract.utils import normalize_path


def get_server_information(
    data_contract_specification: DataContractSpecification,
    server_name: str | None,
    asset_name: str,
) -> dict[str, str]:
    """Returns a dictionary containing server-specific information to be used
    by Dagster for identifying asset locations or connections.

    This function inspects the provided `DataContractSpecification` to locate
    the specified server by name and constructs a dictionary with keys such as
    "dagster/uri" and "dagster/table_name" depending on the server type.

    Parameters:
        data_contract_specification (DataContractSpecification):
            The data contract specification containing server configurations.
        server_name (str | None):
            The name of the server to retrieve information for. If None or not found, returns an empty dict.
        asset_name (str):
            The name of the asset, used for constructing fully qualified table names for certain server types.

    Returns:
        dict[str, str]: A dictionary with keys like "dagster/uri" and/or "dagster/table_name"
        depending on the server type. Returns an empty dictionary if the server is not found
        or if the server type is not recognized or unsupported.
    """
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
            server_information["dagster/uri"] = normalize_path(server.path)
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
