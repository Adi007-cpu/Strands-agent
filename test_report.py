# test_report.py
from report_tool import generate_report

# Simulated outputs from extract_receipt() for 3 fake receipts
receipts = [
    {"vendor": "Starbucks Coffee", "amount": 31.24, "date": "2026-01-10"},
    {"vendor": "Amazon", "amount": 499.00, "date": "2026-01-05"},
    {"vendor": None, "amount": 850.00, "date": None},  # unreadable vendor/date
]

# Simulated outputs from match_transaction() — must be same length/order as receipts
match_results = [
    {"matched": True, "transaction": {"date": "2026-01-10", "description": "STARBUCKS COFFEE", "amount": -31.24}, "confidence": 1.0},
    {"matched": True, "transaction": {"date": "2026-01-05", "description": "AMAZON PAY INDIA", "amount": -499.00}, "confidence": 0.95},
    {"matched": False, "transaction": None, "confidence": 0.0},  # no match found
]

# Simulated outputs from categorize_expense() — same length/order
categorizations = [
    {"category": "Meals & Entertainment", "confidence": "low", "note": "Coffee purchase could be personal or business"},
    {"category": "Office Supplies", "confidence": "low", "note": "Amazon purchase, category unclear"},
    {"category": "Other", "confidence": "low", "note": "No vendor info available"},
]

# Full bank statement — includes an EXTRA charge with no receipt (Uber)
all_transactions = [
    {"date": "2026-01-10", "description": "STARBUCKS COFFEE", "amount": -31.24},
    {"date": "2026-01-05", "description": "AMAZON PAY INDIA", "amount": -499.00},
    {"date": "2026-01-08", "description": "UBER TRIP", "amount": -320.50},  # unmatched on purpose
]

report = generate_report(receipts, match_results, categorizations, all_transactions)

import json
print(json.dumps(report, indent=2, ensure_ascii=False))