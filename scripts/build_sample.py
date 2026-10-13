"""One-off script: build data_sample/ — a seeded 0.5% referential-integrity-preserving
sample of data/ for the Streamlit Cloud free-tier deployment.

Keeps: sampled order_ids (random, seed=42, ~12%) -> order_items/payments/reviews
filtered to those orders -> customers/products/sellers filtered to IDs actually
referenced by the sampled rows. category_translation.csv copied as-is.
"""
import random
import shutil
from pathlib import Path

import pandas as pd

SEED = 42
FRAC = 0.005
SRC = Path(__file__).resolve().parent.parent / "data"
DST = Path(__file__).resolve().parent.parent / "data_sample"
DST.mkdir(exist_ok=True)

rng = random.Random(SEED)
order_ids = pd.read_csv(SRC / "orders.csv", usecols=["order_id"])["order_id"].tolist()
k = int(len(order_ids) * FRAC)
sampled_ids = set(rng.sample(order_ids, k))
print(f"orders: {len(order_ids)} -> sampled {len(sampled_ids)} ({len(sampled_ids)/len(order_ids):.1%})")


def filter_to_orders(name):
    df = pd.read_csv(SRC / f"{name}.csv")
    df = df[df["order_id"].isin(sampled_ids)]
    df.to_csv(DST / f"{name}.csv", index=False)
    print(f"{name}: {len(df)} rows")
    return df


orders = filter_to_orders("orders")
items = filter_to_orders("order_items")
filter_to_orders("payments")
filter_to_orders("reviews")

ref = {
    "customers": ("customer_id", set(orders["customer_id"])),
    "products": ("product_id", set(items["product_id"])),
    "sellers": ("seller_id", set(items["seller_id"])),
}
for name, (col, ids) in ref.items():
    df = pd.read_csv(SRC / f"{name}.csv")
    before = len(df)
    df = df[df[col].isin(ids)]
    df.to_csv(DST / f"{name}.csv", index=False)
    print(f"{name}: {before} -> {len(df)} rows")

shutil.copy(SRC / "category_translation.csv", DST / "category_translation.csv")

total_mb = sum(p.stat().st_size for p in DST.glob("*.csv")) / 1e6
print(f"data_sample/ total: {total_mb:.1f} MB")
assert total_mb <= 10, "sample exceeds 10MB budget"
print("OK")
