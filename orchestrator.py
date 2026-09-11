# orchestrator.py
import os
import glob
from dotenv import load_dotenv
from strands import Agent
from strands.models.openai import OpenAIModel

from extract_receipt import extract_receipt
from bank_tools import parse_bank_statement, match_transaction
from categorize_tool import categorize_expense
from report_tool import generate_report

load_dotenv()

_model = OpenAIModel(
    client_args={
        "api_key": os.getenv("GROQ_API_KEY"),
        "base_url": "https://api.groq.com/openai/v1",
    },
    model_id="openai/gpt-oss-120b",
)


def list_receipt_files(folder_path: str) -> list[str]:
    patterns = ["*.jpg", "*.jpeg", "*.png"]
    files = []
    for pattern in patterns:
        files.extend(glob.glob(os.path.join(folder_path, pattern)))
    return sorted(files)


def run_pipeline(receipts_folder: str, bank_csv: str):
    print("1. Listing receipt files...")
    files = list_receipt_files(receipts_folder)
    print(f"   Found {len(files)} receipts.")

    print("2. Parsing bank statement...")
    bank_txs = parse_bank_statement(bank_csv)

    print("3. Extracting receipts...")
    receipts = []
    for f in files:
        print(f"   Extracting: {f}")
        extracted = extract_receipt(f)
        receipts.append(extracted)

    print("4. Matching transactions...")
    match_results = []
    for r in receipts:
        matched = match_transaction(r, bank_txs)
        match_results.append(matched)

    print("5. Categorizing expenses...")
    categorizations = []
    for r, m in zip(receipts, match_results):
        # Fall back to matched transaction description if receipt vendor is null
        vendor = r.get("vendor")
        if not vendor and isinstance(m, dict):
            vendor = (
                m.get("description")
                or m.get("vendor")
                or m.get("payee")
                or m.get("raw_description")
            )
        cat = categorize_expense(vendor=vendor)
        categorizations.append(cat)

    print("6. Generating raw report...")
    # Passing arguments positionally to avoid parameter keyword mismatches
    report_data = generate_report(
        receipts,
        match_results,
        categorizations,
        bank_txs,
    )

    print("7. Synthesizing final reconciliation via Agent...")
    reporter_agent = Agent(
        model=_model,
        system_prompt=(
            "You are a professional bookkeeping and reconciliation assistant. "
            "Given the raw reconciliation outputs, generate a clear, executive-ready report. "
            "Present matched receipts, unmatched transactions, categorization splits, "
            "and any flagged questions or discrepancies clearly."
        ),
    )

    final_presentation = reporter_agent(
        f"Generate the final presentation report from this reconciliation data:\n{report_data}"
    )
    return final_presentation


if __name__ == "__main__":
    RECEIPTS_FOLDER = "./receipts"
    BANK_CSV = "./sample_bank.csv"

    summary = run_pipeline(RECEIPTS_FOLDER, BANK_CSV)
    print("\n" + "=" * 40 + " FINAL REPORT " + "=" * 40 + "\n")
    print(summary)