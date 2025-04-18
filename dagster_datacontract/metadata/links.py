import dagster as dg


def get_links(links: dict[str, str]) -> dict[str, str]:
    """Return a dictionary with keys prefixed by 'link/' and values as Dagster URL metadata.

    Args:
        links (dict[str, str]): A dictionary where each key is a name/label and each
            value is a URL string.

    Returns:
        dict[str, str]: A dictionary where each key is prefixed with 'link/' and
            each value is a `MetadataValue.url`.
    """
    links = {f"link/{key}": dg.MetadataValue.url(value) for key, value in links.items()}

    return links
