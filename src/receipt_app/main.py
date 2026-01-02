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

def totals_by_category(data: dict) -> dict[str, float]:
    """Aggregate total amount spent per category.

    Ignores receipts with missing/invalid amounts or missing categories.

    Args:
        data: Dictionary mapping filenames to receipt dictionaries.

    Returns:
        Dictionary mapping category name to summed float amount.
    """
    totals: dict[str, float] = {}

    for _name, receipt in data.items():
        if not isinstance(receipt, dict):
            continue

        category = receipt.get("category")
        if not isinstance(category, str) or not category.strip():
            continue

        amt = extract_amount(receipt.get("amount"))
        if amt is None:
            continue

        totals[category] = totals.get(category, 0.0) + amt

    return totals

def plot_expenses_by_category(totals: dict[str, float], outfile: str) -> None:
    """Generate and save a pie chart of expenses by category.

    The chart includes category labels, percent values, and a title. It also
    uses a legend outside the pie and a start angle for readability.

    Args:
        totals: Category totals mapping.
        outfile: Output image filename (e.g., "expenses_by_category.png").
    """
    import matplotlib.pyplot as plt

    # Sort categories for stable, readable output (largest first)
    items = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)
    labels = [k for k, _ in items]
    values = [v for _, v in items]

    # Slightly separate the largest slice for readability
    explode = [0.06] + [0.0] * (len(values) - 1)

    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(
        values,
        labels=None,               # labels via legend (less clutter)
        autopct="%1.1f%%",         # percentage values on slices
        startangle=90,             # readability: start at top
        explode=explode,           # readability: highlight largest
        pctdistance=0.75,          # move percent text inward
    )

    ax.set_title("Expenses by Category")
    ax.axis("equal")  # ensures pie is a circle

    # Put legend outside the pie for readability
    ax.legend(
        wedges,
        labels,
        title="Category",
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
    )

    plt.tight_layout()
    fig.savefig(outfile, dpi=200)
    plt.close(fig)


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
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate a pie chart of expenses by category and save it to a file.",
    )
    parser.add_argument(
        "--plot-out",
        default="expenses_by_category.png",
        help="Output filename for the plot (default: expenses_by_category.png).",
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

    if args.plot:
        totals = totals_by_category(data)
        if not totals:
            raise SystemExit("No valid receipts to plot (missing/invalid amounts or categories).")
        plot_expenses_by_category(totals, args.plot_out)
        print(f"Saved plot to {args.plot_out}")
        return


    if args.print:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()