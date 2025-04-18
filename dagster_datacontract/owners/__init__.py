from datacontract.data_contract import DataContractSpecification


def get_owner(
    data_contract_specification: DataContractSpecification,
    is_team: bool = True,
) -> list[str] | None:
    owner = data_contract_specification.info.owner

    if is_team:
        return [f"team:{owner}"]

    return [owner]
