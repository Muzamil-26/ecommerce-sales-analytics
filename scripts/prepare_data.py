"""Prepare the committed dataset from the raw Olist download.

Raw files live in data/raw/ (gitignored, re-downloadable - see README).
This script produces the committed, analysis-ready CSVs in data/:

  olist_customers_dataset.csv      -> customers.csv
  olist_orders_dataset.csv         -> orders.csv
  olist_order_items_dataset.csv    -> order_items.csv
  olist_order_payments_dataset.csv -> payments.csv
  olist_order_reviews_dataset.csv  -> reviews.csv   (free-text comment columns dropped)
  olist_products_dataset.csv       -> products.csv
  olist_sellers_dataset.csv        -> sellers.csv
  product_category_name_translation.csv -> category_translation.csv (BOM stripped)

Why the reviews file is trimmed: the free-text review_comment_title /
review_comment_message columns are mostly Portuguese free text, are not used
by any analysis in this project (only review_score is), and dropping them
keeps the committed data under the ~60MB free-hosting limit.

Pure standard library - no dependencies needed.
"""

import csv
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
DATA = ROOT / "data"

# raw filename -> committed filename (straight copies)
COPIES = {
    "olist_customers_dataset.csv": "customers.csv",
    "olist_orders_dataset.csv": "orders.csv",
    "olist_order_payments_dataset.csv": "payments.csv",
    "olist_products_dataset.csv": "products.csv",
    "olist_sellers_dataset.csv": "sellers.csv",
}

# order_items.csv keeps the analytical columns; shipping_limit_date (an internal
# seller deadline, unused by every analysis here) is dropped to save ~2MB.
ITEM_KEEP = [
    "order_id",
    "order_item_id",
    "product_id",
    "seller_id",
    "price",
    "freight_value",
]

REVIEW_KEEP = [
    "review_id",
    "order_id",
    "review_score",
    "review_creation_date",
    "review_answer_timestamp",
]


def main() -> None:
    if not RAW.exists():
        raise SystemExit(
            f"Raw data not found in {RAW}. Download the Olist dataset "
            "(see README) and unzip it into data/raw/ first."
        )
    DATA.mkdir(parents=True, exist_ok=True)

    for src_name, dst_name in COPIES.items():
        src = RAW / src_name
        if not src.exists():
            raise SystemExit(f"Missing raw file: {src}")
        shutil.copyfile(src, DATA / dst_name)
        print(f"copied {dst_name}")

    # order_items.csv: keep only the analytical columns
    with open(RAW / "olist_order_items_dataset.csv", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        item_rows = [{k: row[k] for k in ITEM_KEEP} for row in reader]
    with open(DATA / "order_items.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ITEM_KEEP)
        writer.writeheader()
        writer.writerows(item_rows)
    print(f"order_items.csv: {len(item_rows):,} rows (dropped shipping_limit_date)")

    # reviews.csv: keep only the analytical columns
    with open(RAW / "olist_order_reviews_dataset.csv", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = [{k: row[k] for k in REVIEW_KEEP} for row in reader]
    with open(DATA / "reviews.csv", "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=REVIEW_KEEP)
        writer.writeheader()
        writer.writerows(rows)
    print(f"reviews.csv: {len(rows):,} rows (dropped review_comment_title/message)")

    # category_translation.csv: strip the UTF-8 BOM so every tool reads headers cleanly
    with open(
        RAW / "product_category_name_translation.csv", encoding="utf-8-sig"
    ) as fh:
        text = fh.read()
    with open(DATA / "category_translation.csv", "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    print("category_translation.csv: BOM stripped")

    total_mb = sum(p.stat().st_size for p in DATA.glob("*.csv")) / 1e6
    print(f"committed data size: {total_mb:.1f} MB")


if __name__ == "__main__":
    main()
