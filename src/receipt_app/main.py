# main.py
import json
import argparse
from datetime import date
from . import file_io as io_mod
from . import gpt


def process_directory(dirpath: str) -> dict:
    """Process all receipt images in a directory and extract fields."""
    results = {}
    for name, path in io_mod.list_files(dirpath):
        image_b64 = io_mod.encode_file(path)
        data = gpt.extract_receipt_info(image_b64)
        results[name] = data
    return results


def parse_iso_date(value: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD) into a datetime.date.

    Args:
        value: Date string in ISO format YYYY-MM-DD.

    Returns:
        Parsed datetime.date.

    Raises:
        ValueError: If the value is not a valid ISO date.
    """
    return date.fromisoformat(value)


def extract_receipt_iso_date(receipt_date_value) -> date | None:
    """Try to interpret the model's receipt 'date' field as a date.

    We accept:
    - YYYY-MM-DD (ISO)
    - YYYY/MM/DD
    - MM/DD/YYYY

    Anything else is treated as invalid.

    Args:
        receipt_date_value: The 'date' field from the model output.

    Returns:
        A datetime.date if parsing succeeds, otherwise None.
    """
    if not isinstance(receipt_date_value, str):
        return None

    s = receipt_date_value.strip()
    if not s:
        return None

    # Keep only the date portion if model included time.
    # e.g. "2025-09-30 20:15" -> "2025-09-30"
    s = s.split()[0]

    # Normalize separators
    s_norm = s.replace("/", "-")

    # Try ISO first: YYYY-MM-DD
    try:
        return date.fromisoformat(s_norm)
    except ValueError:
        pass

    # Try MM-DD-YYYY (from MM/DD/YYYY normalized)
    parts = s_norm.split("-")
    if len(parts) == 3:
        p1, p2, p3 = parts
        # Heuristic: if last part has 4 digits, interpret as MM-DD-YYYY
        if len(p3) == 4 and p1.isdigit() and p2.isdigit() and p3.isdigit():
            mm = int(p1)
            dd = int(p2)
            yyyy = int(p3)
            try:
                return date(yyyy, mm, dd)
            except ValueError:
                return None

    return None


def extract_amount(value) -> float | None:
    """Validate and return numeric receipt amount as float, else None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    # We already sanitize "$" in gpt.py, but stay defensive
    if isinstance(value, str):
        s = value.strip().replace("$", "").replace(",", "")
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None
    return None


def compute_expenses(data: dict, start: date, end: date) -> float:
    """Sum amounts for receipts whose dates fall within [start, end]."""
    total = 0.0
    for _name, receipt in data.items():
        if not isinstance(receipt, dict):
            continue

        d = extract_receipt_iso_date(receipt.get("date"))
        if d is None:
            continue
        if d < start or d > end:
            continue

        amt = extract_amount(receipt.get("amount"))
        if amt is None:
            continue

        total += amt

    return total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dirpath")
    parser.add_argument("--print", action="store_true")
    parser.add_argument(
        "--expenses",
        nargs=2,
        metavar=("START_DATE", "END_DATE"),
        help="Compute total expenses in date range YYYY-MM-DD YYYY-MM-DD",
    )

    args = parser.parse_args()

    data = process_directory(args.dirpath)

    if args.expenses:
        try:
            start = parse_iso_date(args.expenses[0])
            end = parse_iso_date(args.expenses[1])
        except ValueError:
            raise SystemExit("Error: dates must be in ISO format YYYY-MM-DD.")

        if start > end:
            raise SystemExit("Error: start date must be <= end date.")

        total = compute_expenses(data, start, end)
        print(json.dumps({"total": total}, indent=2))
        return


    if args.print:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()