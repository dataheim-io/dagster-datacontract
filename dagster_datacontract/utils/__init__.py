import os
import urllib.parse


def normalize_path(path: str) -> str:
    parsed = urllib.parse.urlparse(path)

    if not parsed.scheme or parsed.scheme == "file":
        full_path = os.path.abspath(os.path.expanduser(path))
        return f"file://{full_path}"
    else:
        return path
