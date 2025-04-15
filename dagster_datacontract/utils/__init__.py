import os
import urllib.parse


def normalize_path(path: str) -> str:
    """Normalizes a file path to ensure it is returned in a consistent URI format.

    This function checks if the provided path is a local file path (with no scheme
    or with the 'file' scheme) and converts it into a fully qualified file URI.
    If the path already has a non-'file' scheme (e.g., 's3://', 'http://'),
    it is returned unchanged.

    Parameters:
        path (str): The input file path. This can be a relative or absolute local path,
                    a path starting with `~`, or a URI with a supported scheme.

    Returns:
        str: A normalized path string:
             - If the input is a local path or has a "file" scheme, returns it in the form "file:///absolute/path".
             - If the input has another scheme (e.g., "s3://", "http://"), returns it unchanged.
    """
    parsed = urllib.parse.urlparse(path)

    if not parsed.scheme or parsed.scheme == "file":
        full_path = os.path.abspath(os.path.expanduser(path))
        return f"file://{full_path}"
    else:
        return path
