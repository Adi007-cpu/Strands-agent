from bank_tools import parse_bank_statement, match_transaction

txns = parse_bank_statement("sample_bank.csv")
receipt = {"vendor": None, "amount": 31.24, "date": None}
result = match_transaction(receipt, txns)
print(result)