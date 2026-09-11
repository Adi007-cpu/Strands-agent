# report_tool.py
from strands import tool
from datetime import datetime


@tool
def generate_report(receipts: list[dict], match_results: list[dict], categorizations: list[dict], all_transactions: list[dict]) -> dict:
    """
    Compiles the final reconciliation report from all processed data.

    Args:
        receipts: list of extract_receipt() outputs, one per receipt processed.
        match_results: list of match_transaction() outputs, same order/length as receipts.
        categorizations: list of categorize_expense() outputs, same order/length as receipts.
        all_transactions: full list of bank transactions from parse_bank_statement(), used to find
                           bank charges that had NO matching receipt at all.

    Returns:
        dict with keys: summary, matched, unmatched_receipts, unmatched_transactions,
                         flagged_questions, category_breakdown
    """
    matched = []
    unmatched_receipts = []
    flagged_questions = []
    category_totals: dict[str, float] = {}
    matched_txn_keys = set()

    for i, receipt in enumerate(receipts):
        match = match_results[i] if i < len(match_results) else {"matched": False}
        cat = categorizations[i] if i < len(categorizations) else {"category": "Other", "confidence": "low"}

        entry = {
            "vendor": receipt.get("vendor"),
            "amount": receipt.get("amount"),
            "date": receipt.get("date"),
            "category": cat.get("category"),
            "category_confidence": cat.get("confidence"),
        }

        if match.get("matched"):
            entry["bank_transaction"] = match["transaction"]
            entry["match_confidence"] = match.get("confidence")
            matched.append(entry)

            # Track this transaction as accounted for
            txn = match["transaction"]
            matched_txn_keys.add((txn.get("date"), txn.get("amount")))

            # Flag low-confidence categorization even if matched
            if cat.get("confidence") == "low":
                flagged_questions.append(
                    f"Vendor '{receipt.get('vendor') or 'unknown'}' (₹{receipt.get('amount')}) was categorized as "
                    f"'{cat.get('category')}' with low confidence — {cat.get('note', 'please confirm this is correct')}."
                )
        else:
            unmatched_receipts.append(entry)
            flagged_questions.append(
                f"No matching bank transaction found for receipt: vendor '{receipt.get('vendor') or 'unknown'}', "
                f"amount ₹{receipt.get('amount')}, date {receipt.get('date') or 'unknown'} — was this paid another way, "
                f"or is this a duplicate/incorrect receipt?"
            )

        # Running category totals (only count amounts we actually have)
        if entry["amount"] is not None:
            category_totals[entry["category"]] = category_totals.get(entry["category"], 0) + entry["amount"]

    # Find bank transactions with NO receipt at all
    unmatched_transactions = []
    for txn in all_transactions:
        key = (txn.get("date"), txn.get("amount"))
        if key not in matched_txn_keys:
            unmatched_transactions.append(txn)
            flagged_questions.append(
                f"Bank charge of ₹{txn.get('amount')} on {txn.get('date')} ('{txn.get('description')}') has no "
                f"matching receipt — was this a business or personal expense?"
            )

    total_spend = sum(r["amount"] for r in (matched + unmatched_receipts) if r.get("amount") is not None)

    summary = {
        "total_receipts_processed": len(receipts),
        "matched_count": len(matched),
        "unmatched_receipts_count": len(unmatched_receipts),
        "unmatched_bank_charges_count": len(unmatched_transactions),
        "total_spend": round(total_spend, 2),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

    return {
        "summary": summary,
        "matched": matched,
        "unmatched_receipts": unmatched_receipts,
        "unmatched_transactions": unmatched_transactions,
        "flagged_questions": flagged_questions,
        "category_breakdown": {k: round(v, 2) for k, v in category_totals.items()},
    }