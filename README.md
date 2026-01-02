# Receipt App

A small command-line Python application that processes a folder of receipt images and uses the OpenAI API to extract structured information such as date, total amount, vendor, and category.

The program outputs a single JSON dictionary mapping each receipt filename to its extracted fields.

---

## Project Structure

```
lab_1_repo/
├── src/
│   └── receipt_app/
│       ├── __init__.py
│       ├── main.py
│       ├── gpt.py
│       └── file_io.py
├── receipts/
│   └── sample receipt images
├── pyproject.toml
├── Makefile
└── README.md
```

---

## Requirements

- Python 3.10+
- An OpenAI API key
- Conda or virtualenv recommended

---

## Setup

1. Create and activate your environment (conda or venv).

2. Install the project and dependencies:

```bash
pip install -e .
```

3. Set your OpenAI API key:

### Windows (cmd / Anaconda Prompt)
```bash
set OPENAI_API_KEY=YOUR_API_KEY_HERE
```

### macOS / Linux
```bash
export OPENAI_API_KEY=YOUR_API_KEY_HERE
```

---

## Usage

Run the application on a folder of receipt images:

```bash
python -m receipt_app.main receipts --print
```

If you added the console script entry point:

```bash
receipt-app receipts
```

The program prints JSON output to stdout.

---

## Output Format

Example:

```json
{
  "receipt_1.jpg": {
    "date": "2024-01-12",
    "vendor": "Walmart",
    "amount": 23.45,
    "category": "groceries"
  }
}
```

If a field cannot be determined, the value will be `null`.

---

## Notes

- Receipt images are not included in version control.
- This project uses the OpenAI API and requires internet access.
- The codebase follows a standard `src/` Python package layout.

---

## License

MIT License
