# extract_receipt.py
import os
import json
import re
import io
from dotenv import load_dotenv
from strands import tool, Agent
from strands.models.openai import OpenAIModel
from PIL import Image

load_dotenv()

_model = OpenAIModel(
    client_args={
        "api_key": os.getenv("GROQ_API_KEY"),
        "base_url": "https://api.groq.com/openai/v1",
    },
    model_id="qwen/qwen3.6-27b",  # swapped from qwen3.8 — separate, unused daily quota
)

EXTRACTION_SYSTEM_PROMPT = """You are a receipt data extraction assistant.
You will be shown a receipt image directly. Respond with ONLY a valid JSON object
in this exact format, and nothing else:

{"vendor": "<vendor name or null>", "amount": <total as a number or null>, "date": "<YYYY-MM-DD or null>"}

Rules:
- Dates on receipts are usually in DD/MM/YY or DD/MM/YYYY format unless clearly stated otherwise.
- If a field is blank, unreadable, or missing, use null.
- "amount" must be a plain number (no currency symbols, no commas).
- Do not include any explanation, markdown, or text outside the JSON object.
"""


def _load_and_resize_image(image_path: str, max_width: int = 800) -> tuple[bytes, str]:
    """Resizes an image to reduce token usage, returns (bytes, format)."""
    img = Image.open(image_path)
    img_format = "jpeg" if img.format in (None, "JPEG") else img.format.lower()

    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85)
    return buffer.getvalue(), "jpeg"


@tool
def extract_receipt(image_path: str) -> dict:
    """
    Extracts vendor, amount, and date from a receipt image.

    Args:
        image_path: Path to the receipt image file (jpg/png).

    Returns:
        dict with keys: vendor (str|None), amount (float|None), date (str|None), raw_response (str)
    """
    extractor = Agent(model=_model, system_prompt=EXTRACTION_SYSTEM_PROMPT)

    try:
        image_bytes, img_format = _load_and_resize_image(image_path)
    except FileNotFoundError:
        return {"vendor": None, "amount": None, "date": None, "raw_response": "", "error": f"File not found: {image_path}"}

    try:
        response = extractor([
            {"text": "Extract the vendor, amount, and date from this receipt."},
            {"image": {"format": img_format, "source": {"bytes": image_bytes}}},
        ])
        text = str(response).strip()
    except Exception as e:
        return {"vendor": None, "amount": None, "date": None, "raw_response": "", "error": str(e)}

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {"vendor": None, "amount": None, "date": None, "raw_response": text, "error": "No JSON found"}

    try:
        parsed = json.loads(match.group(0))
        parsed["raw_response"] = text
        return parsed
    except json.JSONDecodeError:
        return {"vendor": None, "amount": None, "date": None, "raw_response": text, "error": "JSON parse failed"}


if __name__ == "__main__":
    result = extract_receipt("./sample_receipt.png")
    print(result)