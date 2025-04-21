from collections.abc import Iterable


def combine_parts(parts: Iterable[str | None], delimiter: str = "_") -> str:
    """
    Combine multiple optional strings using a specified delimiter.

    This function takes an iterable of optional strings and joins the non-None,
    non-empty strings using the given delimiter. None values and empty strings
    are ignored. If all values are None or empty, the result is an empty string.

    Args:
        parts (Iterable[Optional[str]]): An iterable of strings or None values to combine.
        delimiter (str): A string used to separate the non-None parts. Defaults to "_".

    Returns:
        str: A single combined string of all non-None, non-empty parts separated by the delimiter.

    Examples:
        >>> combine_parts(["v1", "2023", None])
        'v1_2023'

        >>> combine_parts([None, None])
        ''

        >>> combine_parts(["", "alpha", None])
        'alpha'
    """
    return delimiter.join(filter(None, parts))
