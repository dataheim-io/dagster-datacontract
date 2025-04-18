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

    Server information can be obtained from: https://datacontract.com/#server-object

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
            server_information["azure/storage_account"] = server.storageAccount
            server_information["file/format"] = server.format
            server_information["file/delimiter"] = server.delimiter
        case "bigquery":
            server_information["bigquery/project"] = server.project
            server_information["bigquery/dataset"] = server.dataset
        case "databricks":
            server_information["dagster/uri"] = server.host
            server_information["dagster/table_name"] = (
                f"{server.catalog}.{server.schema}.{asset_name}"
            )
        case "glue":
            server_information = {}
        case "kafka":
            server_information["dagster/uri"] = server.host
            server_information["kafka/topic"] = server.topic
            server_information["kafka/format"] = server.format
        case "kinesis":
            server_information["kinesis/stream"] = server.stream
            server_information["kinesis/region"] = server.region
            server_information["kinesis/format"] = server.format
        case "local":
            server_information["dagster/uri"] = normalize_path(server.path)
            server_information["file/format"] = server.format
        case "oracle":
            server_information["dagster/uri"] = f"{server.host}:{server.port}"
            server_information["oracle/service_name"] = server.serviceName
        case "postgres":
            server_information["dagster/uri"] = f"{server.host}:{server.port}"
            server_information["dagster/table_name"] = (
                f"{server.database}.{server.schema}.{asset_name}"
            )
        case "pubsub":
            server_information["pubsub/project"] = server.project
            server_information["pubsub/topic"] = server.topic
        case "redshift":
            server_information["dagster/uri"] = server.endpoint
            server_information["dagster/table_name"] = (
                f"{server.database}.{server.schema}.{asset_name}"
            )
            server_information["redshift/account"] = server.account
            server_information["redshift/host"] = server.host
            server_information["redshift/port"] = server.port
            server_information["redshift/cluster"] = server.clusterIdentifier
        case "s3":
            server_information["dagster/uri"] = server.location
            server_information["s3/endpoint"] = server.endpointUrl
            server_information["file/format"] = server.format
            server_information["file/delimiter"] = server.delimiter
        case "sftp":
            server_information["dagster/uri"] = server.location
            server_information["file/format"] = server.format
            server_information["file/delimiter"] = server.delimiter
        case "snowflake":
            server_information["dagster/table_name"] = (
                f"{server.database}.{server.schema}.{asset_name}"
            )
            server_information["snowflake/account"] = server.account
        case "sqlserver":
            server_information["dagster/table_name"] = (
                f"{server.database}.{server.schema}.{asset_name}"
            )
            server_information["sqlserver/host"] = server.host
            server_information["sqlserver/port"] = server.port
            server_information["sqlserver/driver"] = server.driver
        case "trino":
            server_information["dagster/uri"] = f"{server.host}:{server.port}"
            server_information["dagster/table_name"] = (
                f"{server.catalog}.{server.schema}.{asset_name}"
            )
        case _:
            server_information = {}

    return server_information
