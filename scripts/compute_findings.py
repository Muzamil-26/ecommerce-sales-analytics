"""Compute the headline numbers used in README.md and the notebooks.

Run:  .venv/bin/python scripts/compute_findings.py   (or any python with pandas)
Prints a findings summary; every number is computed from data/, never invented.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import pandas as pd  # noqa: E402

from ecommerce import build_item_facts, build_order_facts, build_rfm  # noqa: E402

facts = build_order_facts()
items = build_item_facts()
rfm = build_rfm()

delivered = facts[facts["order_status"] == "delivered"]
revenue = delivered["total_payment"].sum()
orders_n = facts["order_id"].nunique()
delivered_n = delivered["order_id"].nunique()

print("=== HEADLINE ===")
print(f"orders_total: {orders_n:,}")
print(f"orders_delivered: {delivered_n:,}")
print(f"total_revenue: R$ {revenue:,.2f}")
print(f"aov: R$ {revenue/delivered_n:,.2f}")
print(f"date_range: {facts['order_purchase_timestamp'].min().date()} to {facts['order_purchase_timestamp'].max().date()}")
print(f"customers_unique: {facts['customer_unique_id'].nunique():,}")
print(f"avg_review: {delivered['review_score'].mean():.2f}")

print("\n=== MONTHLY REVENUE (delivered) ===")
monthly = delivered.groupby("order_month")["total_payment"].sum()
for m, v in monthly.items():
    print(f"{m}: R$ {v:,.0f}")
peak = monthly.idxmax()
print(f"peak_month: {peak} R$ {monthly.max():,.0f}")

print("\n=== TOP 10 CATEGORIES BY REVENUE (delivered items) ===")
cat = (
    items[items["order_status"] == "delivered"]
    .groupby("category_en")
    .agg(revenue=("price", "sum"), orders=("order_id", "nunique"))
    .sort_values("revenue", ascending=False)
)
for c, row in cat.head(10).iterrows():
    print(f"{c}: R$ {row['revenue']:,.0f} ({row['orders']:,} orders)")
print(f"top3_share: {cat['revenue'].head(3).sum()/cat['revenue'].sum()*100:.1f}%")

print("\n=== TOP STATES BY REVENUE ===")
st = delivered.groupby("customer_state").agg(revenue=("total_payment", "sum"), orders=("order_id", "nunique")).sort_values("revenue", ascending=False)
for s, row in st.head(8).iterrows():
    print(f"{s}: R$ {row['revenue']:,.0f} ({row['orders']:,} orders)")
print(f"SP_share: {st['revenue'].iloc[0]/st['revenue'].sum()*100:.1f}%")

print("\n=== REPEAT CUSTOMERS ===")
cust_orders = delivered.groupby("customer_unique_id")["order_id"].nunique()
repeat_rate = (cust_orders > 1).mean()
print(f"repeat_rate: {repeat_rate*100:.1f}% ({(cust_orders>1).sum():,} of {len(cust_orders):,} customers)")

print("\n=== DELIVERY PERFORMANCE ===")
dd = delivered.dropna(subset=["delay_days"])
late_rate = dd["is_late"].mean()
print(f"late_rate: {late_rate*100:.1f}% ({dd['is_late'].sum():,} of {len(dd):,} delivered orders)")
print(f"avg_delay_when_late: {dd.loc[dd['is_late'],'delay_days'].mean():.1f} days")
print(f"avg_early_when_ontime: {dd.loc[~dd['is_late'],'delay_days'].mean():.1f} days")

print("\n=== DELIVERY vs REVIEWS ===")
rev = delivered.dropna(subset=["review_score", "delay_days"])
late_rev = rev[rev["is_late"]]["review_score"].mean()
ontime_rev = rev[~rev["is_late"]]["review_score"].mean()
print(f"avg_review_late: {late_rev:.2f}")
print(f"avg_review_ontime: {ontime_rev:.2f}")
print(f"share_5star_ontime: {(rev[~rev['is_late']]['review_score']==5).mean()*100:.1f}%")
print(f"share_5star_late: {(rev[rev['is_late']]['review_score']==5).mean()*100:.1f}%")
print(f"share_1star_late: {(rev[rev['is_late']]['review_score']==1).mean()*100:.1f}%")
print(f"share_1star_ontime: {(rev[~rev['is_late']]['review_score']==1).mean()*100:.1f}%")

print("\n=== PAYMENT MIX ===")
pm = delivered.groupby("payment_type").agg(orders=("order_id", "nunique"), value=("total_payment", "sum"))
pm["share"] = pm["orders"] / pm["orders"].sum() * 100
for p, row in pm.sort_values("orders", ascending=False).iterrows():
    print(f"{p}: {row['share']:.1f}% of orders, avg installments {delivered[delivered['payment_type']==p]['max_installments'].mean():.1f}")

print("\n=== REVIEW SCORE DISTRIBUTION ===")
rs = delivered["review_score"].value_counts(normalize=True).sort_index() * 100
for s, v in rs.items():
    print(f"score {int(s)}: {v:.1f}%")

print("\n=== SEASONALITY (revenue by calendar month, delivered) ===")
seas = delivered.copy()
seas["cal_month"] = seas["order_purchase_timestamp"].dt.month
sm = seas.groupby("cal_month")["total_payment"].sum()
for m, v in sm.items():
    print(f"month {m:02d}: R$ {v:,.0f}")

print("\n=== RFM SEGMENTS ===")
seg = rfm.groupby("segment").agg(customers=("customer_unique_id", "count"), revenue=("monetary", "sum"))
seg["rev_share"] = seg["revenue"] / seg["revenue"].sum() * 100
for s, row in seg.sort_values("customers", ascending=False).iterrows():
    print(f"{s}: {row['customers']:,} customers ({row['customers']/len(rfm)*100:.1f}%), R$ {row['revenue']:,.0f} ({row['rev_share']:.1f}% of revenue)")
print(f"rfm_customers: {len(rfm):,}")

print("\n=== CATEGORY DELIVERY (worst late rates, min 200 orders) ===")
item_ord = items[items["order_status"] == "delivered"].merge(
    facts[["order_id", "is_late", "delay_days"]], on="order_id", how="left"
)
cd = item_ord.groupby("category_en").agg(orders=("order_id", "nunique"), late_rate=("is_late", "mean"), avg_delay=("delay_days", "mean"))
cd = cd[cd["orders"] >= 200].sort_values("late_rate", ascending=False)
for c, row in cd.head(5).iterrows():
    print(f"{c}: late {row['late_rate']*100:.1f}%, avg delay {row['avg_delay']:.1f}d ({row['orders']:,} orders)")
