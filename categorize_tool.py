# categorize_tool.py
import os
from dotenv import load_dotenv
from strands import tool, Agent
from strands.models.openai import OpenAIModel

load_dotenv()

_model = OpenAIModel(
    client_args={
        "api_key": os.getenv("GROQ_API_KEY"),
        "base_url": "https://api.groq.com/openai/v1",
    },
    model_id="openai/gpt-oss-120b",  # good for reasoning/categorization, no vision needed here
)

CATEGORY_SYSTEM_PROMPT = """You are an expense categorization assistant for small-business bookkeeping.
Given a vendor name and/or transaction description, respond with ONLY a valid JSON object in this exact format:

{"category": "<category>", "confidence": "high|medium|low", "note": "<short reason, or null>"}

Use one of these categories: Office Supplies, Software/Subscriptions, Travel, Meals & Entertainment,
Equipment, Utilities, Rent, Professional Services, Marketing, Personal (non-business), Other.

If the vendor/description is ambiguous or could be personal or business, use confidence "low" and
add a short note explaining the ambiguity. Do not include any text outside the JSON object.
"""


@tool
def categorize_expense(vendor: str | None, description: str = "") -> dict:
    """
    Categorizes an expense for tax/bookkeeping purposes based on vendor and/or description.

    Args:
        vendor: Vendor name from the receipt (may be None if unreadable).
        description: Bank transaction description, used as a fallback/supplement.

    Returns:
        dict with keys: category (str), confidence (str), note (str|None)
    """
    categorizer = Agent(model=_model, system_prompt=CATEGORY_SYSTEM_PROMPT)

    input_text = f"Vendor: {vendor or 'unknown'}. Transaction description: {description or 'none'}."
    response = categorizer(input_text)
    text = str(response).strip()

    import json, re
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {"category": "Other", "confidence": "low", "note": "Could not parse categorization"}

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"category": "Other", "confidence": "low", "note": "JSON parse failed"}


if __name__ == "__main__":
    print(categorize_expense("STARBUCKS COFFEE", "STARBUCKS COFFEE"))
    print(categorize_expense(None, "AMAZON PAY INDIA"))