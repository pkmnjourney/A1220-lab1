# gpt.py
import json
from openai import OpenAI

client = OpenAI()

CATEGORIES = [
    "Meals",
    "Transport",
    "Lodging",
    "Office Supplies",
    "Entertainment",
    "Other",
]

def sanitize_amount(data: dict) -> dict:
    """Normalize the 'amount' field in a receipt dictionary.

    Removes a leading '$' if present, converts the amount to float,
    and replaces the value in the input dictionary.

    Args:
        data: Receipt dictionary returned by the language model.

    Returns:
        The same dictionary with a normalized float 'amount' when possible.
        If parsing fails or amount is missing, amount is set to None.
    """
    if not isinstance(data, dict):
        return data

    raw = data.get("amount", None)
    if raw is None:
        return data

    # If it's already a number, just convert to float.
    if isinstance(raw, (int, float)):
        data["amount"] = float(raw)
        return data

    # Otherwise, try to clean a string like "$12.34" or "  $1,234.56  "
    if isinstance(raw, str):
        cleaned = raw.strip().replace("$", "").replace(",", "")
        if cleaned == "":
            data["amount"] = None
            return data
        try:
            data["amount"] = float(cleaned)
        except ValueError:
            data["amount"] = None

    return data


def extract_receipt_info(image_b64: str) -> dict:
    """Extract structured receipt information using the OpenAI API.

    The model attempts to extract the following fields:
    - date
    - amount
    - vendor
    - category (one of predefined categories)

    Args:
        image_b64: Base64-encoded receipt image.

    Returns:
        A dictionary containing the extracted receipt fields.
        Fields that cannot be determined will have a value of None.
    """
    prompt = f"""
        You are an information extraction system.
        Extract ONLY the following fields from the receipt image:

        date: the receipt date as a string
        amount: the total amount paid as it appears on the receipt
        vendor: the merchant or vendor name
        category: one of [{", ".join(CATEGORIES)}]

        Return EXACTLY one JSON object with these four keys and NOTHING ELSE.
        Do not include explanations, comments, or formatting.
        Do not wrap the JSON in markdown.
        If a field cannot be determined, use null.

        The output must be valid JSON.
        """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        seed=43,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        },
                    },
                ],
            }
        ],
    )
    data = json.loads(response.choices[0].message.content)
    return sanitize_amount(data)
