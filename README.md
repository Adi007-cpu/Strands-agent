# AI Bookkeeping Reconciliation Agent

An autonomous AI agent, built with the [Strands Agents SDK](https://strandsagents.com), that automates monthly bookkeeping reconciliation for freelancers and small-business owners.

Built for the **AWS "Agents for Humans" Hackathon** — Professional Agents track.

## The Problem

Freelancers and small-business owners have to do their own bookkeeping every month — going through a pile of receipts and a bank statement, matching them up by hand, figuring out what's a business expense vs. personal, and catching cases where something's missing or doesn't add up. It's boring, error-prone, and eats hours nobody wants to spend.

## What This Agent Does

Feed it two things:
1. A folder of receipt images (jpg/png)
2. A bank statement (CSV)

The agent then, autonomously, without step-by-step guidance:

1. **Reads** each receipt and extracts vendor, amount, and date
2. **Matches** each receipt against the bank statement to confirm the payment actually happened
3. **Categorizes** each expense for tax purposes
4. **Flags problems** — a receipt with no matching bank transaction, a bank charge with no receipt, amounts that don't quite line up
5. **Produces a clean report**, plus a short list of genuine judgment-call questions ("no receipt for this ₹499 charge — was this business or personal?")

The goal isn't to silently guess — it's to do the matching work a person or bookkeeper would do by hand, and surface exactly the uncertain bits for a human to decide on.

## Architecture

```
receipts/ (images)  ─┐
                      ├─► Orchestrator Agent (Strands)
bank_statement.csv ──┘         │
                                ├─► extract_receipt      (vision model reads each receipt)
                                ├─► parse_bank_statement  (CSV → transaction list)
                                ├─► match_transaction     (amount + date + fuzzy vendor matching)
                                ├─► categorize_expense    (tax category judgment call)
                                └─► generate_report       (compiles final summary + flagged questions)
                                        │
                                        ▼
                              Reconciliation Report
                         (matches, mismatches, questions)
```

See `architecture-diagram.png` for a visual version.

## Tech Stack

- **[Strands Agents SDK](https://strandsagents.com)** — agent orchestration and tool-calling
- **Groq API** (OpenAI-compatible) — model inference
  - `qwen/qwen3.6-27b` for receipt image extraction (vision)
  - `openai/gpt-oss-120b` for categorization and orchestration reasoning
- **pandas** — bank statement parsing
- **rapidfuzz** — fuzzy vendor-name matching
- **Pillow** — image preprocessing/resizing before extraction

> **Note on AWS Bedrock:** This project was originally built to run on Amazon Bedrock, as the hackathon recommends. During development, the AWS account used for this project got stuck in an unresolved model-access block (a support case was filed and followed up on, but the issue was not resolved before the deadline). The project was pivoted to run on Groq — Strands' provider-agnostic model design made this a small, contained change rather than a rewrite. Swapping back to Bedrock only requires changing the model configuration in `extract_receipt.py`, `categorize_tool.py`, and `orchestrator.py`.

## Setup

### Prerequisites
- Python 3.10+
- A free [Groq API key](https://console.groq.com)

### Installation

```bash
git clone https://github.com/Adi007-cpu/Strands-agent.git
cd Strands-agent

python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install strands-agents strands-agents-tools pandas rapidfuzz pillow python-dotenv
```

### Configuration

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

### Running

Sample receipts and a sample bank statement are included (`receipts/`, `sample_bank.csv`) so you can test immediately:

```bash
python orchestrator.py
```

This will process every receipt image in `receipts/` against `sample_bank.csv` and print a full reconciliation report to the terminal.

To use your own data, replace the contents of `receipts/` with your own receipt images and point `BANK_CSV` in `orchestrator.py` at your own bank statement CSV (expected columns: `date`, `description`, `amount`).

### Generating more synthetic test receipts

```bash
python receipt_generator.py
```

This creates additional synthetic receipt images (with known ground-truth values in matching `.json` files) in `generated_receipts/`, useful for testing extraction accuracy.

## Project Structure

| File | Purpose |
|---|---|
| `orchestrator.py` | Main entry point — runs the full agent pipeline |
| `extract_receipt.py` | Tool: reads a receipt image, extracts vendor/amount/date |
| `bank_tools.py` | Tools: parses bank CSV, matches receipts to transactions |
| `categorize_tool.py` | Tool: categorizes an expense for tax purposes |
| `report_tool.py` | Tool: compiles the final reconciliation report |
| `receipt_generator.py` | Utility: generates synthetic test receipts |
| `sample_bank.csv` | Sample bank statement for testing |
| `receipts/` | Sample receipt images for testing |

## Why This Fits "Professional Agents"

This agent takes on repetitive, judgment-heavy work that eats a small-business owner's time — and does it end-to-end, autonomously, rather than requiring step-by-step guidance. It's a single, focused pipeline (parse → match → categorize → flag → report), buildable and demoable solo, with no sprawling integrations required.

## License

MIT — see [LICENSE](./LICENSE).