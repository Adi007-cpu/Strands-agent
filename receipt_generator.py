"""
Synthetic Receipt Generator
---------------------------

Generates 5 realistic-looking synthetic receipts for OCR / document-AI testing.

Output:
    generated_receipts/
        receipt_001.png
        receipt_001.json
        receipt_002.png
        receipt_002.json
        ...

Dependencies:
    pip install pillow

IMPORTANT:
    These are synthetic test documents. Vendor names, amounts, dates, and IDs
    are all randomly generated and do not represent real transactions.
"""

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
import json
import os
import random

random.seed(42)

OUTPUT_DIR = "generated_receipts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VENDORS = [
    "Village Market", "Cafe Coffee Day", "Big Bazaar", "Reliance Fresh",
    "Urban Threads Clothing", "Spice Route Restaurant", "QuickMart Stores",
]

ITEMS_POOL = [
    ("Coffee", 120), ("Sandwich", 180), ("Notebook", 60), ("Pen Set", 90),
    ("Milk 1L", 55), ("Bread Loaf", 45), ("T-Shirt", 450), ("Groceries Pack", 320),
]


def _load_font(size: int):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", size)
    except Exception:
        return ImageFont.load_default()


def generate_receipt(index: int):
    vendor = random.choice(VENDORS)
    date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime("%d/%m/%y")

    num_items = random.randint(1, 4)
    items = random.sample(ITEMS_POOL, num_items)

    total = Decimal("0")
    lines = []
    for name, price in items:
        qty = random.randint(1, 3)
        line_total = Decimal(price * qty)
        total += line_total
        lines.append((name, qty, price, line_total))

    total = total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # --- Draw the receipt image ---
    width, height = 500, 500 + (num_items * 30)
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    font_title = _load_font(28)
    font_normal = _load_font(18)
    font_bold = _load_font(20)

    y = 20
    draw.text((width // 2 - len(vendor) * 7, y), vendor, font=font_title, fill="black")
    y += 45
    draw.text((30, y), f"Date: {date}", font=font_normal, fill="black")
    y += 30
    draw.line((30, y, width - 30, y), fill="black", width=2)
    y += 20

    for name, qty, price, line_total in lines:
        draw.text((30, y), f"{name} x{qty}", font=font_normal, fill="black")
        draw.text((width - 130, y), f"Rs {line_total}", font=font_normal, fill="black")
        y += 30

    y += 10
    draw.line((30, y, width - 30, y), fill="black", width=2)
    y += 20
    draw.text((30, y), "TOTAL:", font=font_bold, fill="black")
    draw.text((width - 150, y), f"Rs {total}", font=font_bold, fill="black")

    filename_base = f"receipt_{index:03d}"
    img_path = os.path.join(OUTPUT_DIR, f"{filename_base}.png")
    img.save(img_path)

    # --- Save ground-truth JSON ---
    truth = {
        "vendor": vendor,
        "amount": float(total),
        "date": datetime.strptime(date, "%d/%m/%y").strftime("%Y-%m-%d"),
        "items": [{"name": n, "qty": q, "unit_price": p} for n, q, p, _ in lines],
    }
    json_path = os.path.join(OUTPUT_DIR, f"{filename_base}.json")
    with open(json_path, "w") as f:
        json.dump(truth, f, indent=2)

    return truth


if __name__ == "__main__":
    all_truths = []
    for i in range(1, 6):
        truth = generate_receipt(i)
        all_truths.append(truth)
        print(f"Generated receipt_{i:03d}: {truth['vendor']} - Rs {truth['amount']} - {truth['date']}")

    print(f"\nDone. {len(all_truths)} receipts saved to '{OUTPUT_DIR}/'")