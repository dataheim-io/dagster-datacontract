from datacontract.data_contract import DataContractSpecification


def get_owner(
    data_contract_specification: DataContractSpecification,
    is_team: bool = True,
) -> list[str] | None:
    """Return the owner of a data contract, optionally formatted as a team identifier.

    Args:
        data_contract_specification (DataContractSpecification): The data contract specification containing ownership metadata.
        is_team (bool, optional): If True, formats the owner as a team identifier (e.g., 'team:owner').
                                  If False, returns the raw owner string. Defaults to True.

    Returns:
        list[str] | None: A list containing the owner string, formatted depending on `is_team`, or None if no owner is found.
    """
    owner = data_contract_specification.info.owner

    if is_team:
        return [f"team:{owner}"]

    return [owner]
