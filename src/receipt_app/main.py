# main.py
import json
import argparse
from . import file_io as io_mod
from . import gpt


def process_directory(dirpath: str) -> dict:
    """Process all receipt images in a directory.

    Reads each file, encodes it as base64, sends it to the
    GPT extraction function, and collects the results.

    Args:
        dirpath: Path to a directory containing receipt images.

    Returns:
        A dictionary mapping filenames to extracted receipt data.
    """
    results = {}
    for name, path in io_mod.list_files(dirpath):
        image_b64 = io_mod.encode_file(path)
        data = gpt.extract_receipt_info(image_b64)
        results[name] = data
    return results


def main() -> None:
    """Command-line entry point for the receipt application.

    Parses command-line arguments, processes the receipt directory,
    and optionally prints the extracted data as formatted JSON.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("dirpath")
    parser.add_argument("--print", action="store_true")
    args = parser.parse_args()

    data = process_directory(args.dirpath)
    if args.print:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()