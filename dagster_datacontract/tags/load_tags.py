import re

from loguru import logger


def get_tags(
    tags_list: list[str] | None,
) -> dict[str, str]:
    """Safely load tags from data contract.

    More information about Dagster tags:
    https://docs.dagster.io/guides/build/assets/metadata-and-tags/tags
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
