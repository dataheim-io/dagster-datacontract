import re

from loguru import logger


def get_tags(
    tags_list: list[str] | None,
) -> dict[str, str]:
    """Parse and validate a list of string tags into a dictionary format.

    Each tag in the input list should be in the form "key:value" or simply "key".
    - Keys must match the pattern: ^[\w.-]{1,63}$
    - Values (if provided) must match the pattern: ^[\w.-]{0,63}$

    Invalid tags (those that do not match the expected format) will be ignored,
    and a warning will be logged.

    More information about Dagster tags:
    https://docs.dagster.io/guides/build/assets/metadata-and-tags/tags

    Args:
        tags_list (list[str] | None): A list of tags as strings. Each tag may be
            formatted as "key:value" or just "key". If None, an empty dict is returned.

    Returns:
        dict[str, str]: A dictionary of validated tags, where keys are tag names
        and values are tag values (empty string if not provided).
    """
    key_pattern = re.compile(r"^[\w.-]{1,63}$")
    val_pattern = re.compile(r"^[\w.-]{0,63}$")

    tags = {}

    for item in tags_list:
        if ":" in item:
            key, val = map(str.strip, item.split(":", 1))
        else:
            key, val = item.strip(), ""

        if key_pattern.match(key) and val_pattern.match(val):
            tags[key] = val
        else:
            logger.warning(f"Ignoring invalid tag: {item}")

    return tags
