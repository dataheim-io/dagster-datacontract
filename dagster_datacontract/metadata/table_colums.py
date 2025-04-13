import dagster as dg
from datacontract.model.data_contract_specification import Field

from dagster_datacontract.tags.load_tags import get_tags


def get_other_item(name: str, column_field: Field) -> list[str] | None:
    """Retrieve a list containing a single formatted string representing an attribute of a Field, if it exists.

    Args:
    name (str): The name of the attribute to fetch from the Field.
    column_field (Field): The Field instance from which to extract the attribute.

    Returns:
        list[str] | None: A list with a formatted string (e.g., "format=csv")
            if the attribute exists and is truthy, otherwise an empty list.
    """
    value = getattr(column_field, name, None)
    return [f"{name}={value}"] if value else []


def get_table_column_constraints(column_field: Field) -> dg.TableColumnConstraints:
    """Convert a Field object to Dagster TableColumnConstraints, including nullability, uniqueness, and other properties.

    Args:
        column_field (Field): A data contract field specification containing
            column metadata.

    Returns:
        dg.TableColumnConstraints: A Dagster representation of the field's
            column constraints.
    """
    nullable = column_field.required if column_field.required else True
    unique = column_field.unique if column_field.unique else False
    other = [
        *(get_other_item("title", column_field)),
        *(get_other_item("primaryKey", column_field)),
        *(get_other_item("format", column_field)),
        *(get_other_item("minLength", column_field)),
        *(get_other_item("maxLength", column_field)),
        *(get_other_item("pattern", column_field)),
        *(get_other_item("minimum", column_field)),
        *(get_other_item("exclusiveMinimum", column_field)),
        *(get_other_item("maximum", column_field)),
        *(get_other_item("exclusiveMaximum", column_field)),
        *(get_other_item("pii", column_field)),
        *(get_other_item("classification", column_field)),
    ]

    return dg.TableColumnConstraints(
        nullable=nullable,
        unique=unique,
        other=other,
    )


def get_table_column(column_name: str, column_field: Field) -> dg.TableColumn:
    """Create a Dagster TableColumn from a given column name and Field metadata.

    Args:
        column_name (str): The name of the column.
        column_field (Field): The Field instance containing metadata such as
            type, description, constraints, and tags.

    Returns:
        dg.TableColumn: A Dagster TableColumn object representing the column
            definition.
    """
    return dg.TableColumn(
        name=column_name,
        type=column_field.type,
        description=column_field.description,
        constraints=get_table_column_constraints(column_field),
        tags=get_tags(column_field.tags),
    )
