import textwrap
from typing import Any

from datacontract.data_contract import DataContractSpecification


def get_description(
    asset_name: str,
    data_contract_specification: DataContractSpecification,
    config: dict[str, Any] | None = None,
    separator: str = "\n",
) -> str | None:
    """Load and return a formatted description string based on the data contract specification.

    This method composes a description by pulling text from different parts
    of the data contract specification (e.g., model and info descriptions),
    joining them using the specified separator.

    Args:
        config (dict[str, Any] | None, optional): A configuration dictionary
            specifying the order in which to concatenate the description parts.
            Defaults to `{"order": ["model", "info"]}`.
        separator (str, optional): A string used to separate different parts
            of the description. Defaults to a newline character (`"\n"`).

    Returns:
        str | None: A single string combining the specified description parts
        if available, otherwise `None`.
    """
    default_config = {"order": ["model", "info"]}

    configuration = default_config | (config or {})

    descriptions = {
        "model": data_contract_specification.models.get(asset_name).description,
        "info": data_contract_specification.info.description,
    }

    parts = []
    for key in configuration["order"]:
        desc = descriptions.get(key).replace("\n", f"{separator}\n")
        if desc:
            parts.append(textwrap.dedent(desc))

    if parts:
        return f"{separator}\n".join(parts)

    return None
