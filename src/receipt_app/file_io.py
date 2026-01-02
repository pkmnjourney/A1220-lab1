# file_io.py
import os
import base64


def encode_file(path: str) -> str:
    """Read a file from disk and encode its contents as base64.

    Args:
        path: Path to the file to be encoded.

    Returns:
        A base64-encoded string of the file contents.
    """
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def list_files(dirpath: str):
    """Yield all files in a directory.

    Args:
        dirpath: Path to a directory.

    Yields:
        Tuples of (filename, full file path) for each file in the directory.
    """
    for name in os.listdir(dirpath):
        path = os.path.join(dirpath, name)
        if os.path.isfile(path):
            yield name, path
