# bank_tools.py
import pandas as pd
from datetime import datetime
from strands import tool
from rapidfuzz import fuzz


@tool
def parse_bank_statement(csv_path: str) -> list[dict]:
    """
    Reads a bank statement CSV and returns a normalized list of transactions.

    Expected columns (case-insensitive): date, description, amount

    Returns:
        List of dicts: [{"date": "2026-01-05", "description": "AMAZON PAY", "amount": -499.0}, ...]
    """
    df = pd.read_csv(csv_path)
    df.columns = [c.strip().lower() for c in df.columns]

    required_cols = {"date", "description", "amount"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Bank statement is missing required columns: {missing}")

    transactions = []
    for _, row in df.iterrows():
        raw_date = str(row["date"]).strip()
        parsed_date = _parse_date(raw_date)

        raw_amount = str(row["amount"]).replace(",", "").replace("₹", "").replace("$", "").strip()
        try:
            amount = float(raw_amount)
        except ValueError:
            amount = None

        transactions.append({
            "date": parsed_date,
            "description": str(row["description"]).strip(),
            "amount": amount,
        })

    return transactions


def _parse_date(raw_date: str) -> str:
    formats_to_try = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y"]
    for fmt in formats_to_try:
        try:
            return datetime.strptime(raw_date, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw_date


@tool
def match_transaction(receipt: dict, transactions: list[dict], date_tolerance_days: int = 3, amount_tolerance: float = 0.01) -> dict:
    """
    Attempts to find a bank transaction matching a given receipt.

    Args:
        receipt: dict with keys "vendor", "amount", "date" (from extract_receipt)
        transactions: list of transaction dicts (from parse_bank_statement)
        date_tolerance_days: how many days apart dates can be and still count as a match
        amount_tolerance: how much amounts can differ and still count as a match

    Returns:
        dict: {"matched": bool, "transaction": dict|None, "confidence": float, "reason": str}
    """
    if receipt.get("amount") is None:
        return {"matched": False, "transaction": None, "confidence": 0.0, "reason": "Receipt has no amount to match against"}

    best_match = None
    best_score = 0.0

    for txn in transactions:
        if txn.get("amount") is None:
            continue

        # Amount check (use absolute value since bank amounts may be negative for debits)
        amount_diff = abs(abs(txn["amount"]) - abs(receipt["amount"]))
        if amount_diff > amount_tolerance:
            continue

        # Date proximity check (only if both dates are present)
        date_score = 1.0
        if receipt.get("date") and txn.get("date"):
            try:
                d1 = datetime.strptime(receipt["date"], "%Y-%m-%d")
                d2 = datetime.strptime(txn["date"], "%Y-%m-%d")
                days_apart = abs((d1 - d2).days)
                if days_apart > date_tolerance_days:
                    continue
                date_score = 1 - (days_apart / (date_tolerance_days + 1))
            except ValueError:
                pass  # unparseable date, don't penalize

        # Vendor name fuzzy match (only if receipt has a vendor)
        vendor_score = 1.0
        if receipt.get("vendor"):
            vendor_score = fuzz.partial_ratio(receipt["vendor"].lower(), txn["description"].lower()) / 100

        combined_score = (date_score * 0.3) + (vendor_score * 0.7)

        if combined_score > best_score:
            best_score = combined_score
            best_match = txn

    if best_match:
        return {"matched": True, "transaction": best_match, "confidence": round(best_score, 2), "reason": "Amount matched within tolerance"}

    return {"matched": False, "transaction": None, "confidence": 0.0, "reason": "No transaction found within amount/date/vendor tolerance"}