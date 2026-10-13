"""Shared data loading, cleaning and feature building for the
E-commerce Sales Analytics project (Olist Brazilian marketplace data).

Used by the notebooks and the Streamlit dashboard so every surface
analyses the exact same cleaned tables.
"""

from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

TIMESTAMP_COLS = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "reviews": ["review_creation_date", "review_answer_timestamp"],
}


def load_all(data_dir: Path | str = DATA_DIR) -> dict[str, pd.DataFrame]:
    """Load every committed CSV into a dict of DataFrames with parsed dates."""
    data_dir = Path(data_dir)
    tables = {}
    for name in [
        "customers",
        "orders",
        "order_items",
        "payments",
        "reviews",
        "products",
        "sellers",
        "category_translation",
    ]:
        df = pd.read_csv(data_dir / f"{name}.csv")
        for col in TIMESTAMP_COLS.get(name, []):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        tables[name] = df
    return tables


def build_order_facts(data_dir: Path | str = DATA_DIR) -> pd.DataFrame:
    """One row per order with customer, payment, item and review facts.

    Adds: total_payment, n_items, item_revenue, freight, review_score,
    delay_days (actual - estimated delivery), is_late, order_month.
    """
    t = load_all(data_dir)
    orders = t["orders"].copy()

    pay_rows = t["payments"].sort_values(["order_id", "payment_sequential"])
    pay = pay_rows.groupby("order_id", as_index=False).agg(
        total_payment=("payment_value", "sum"),
        payment_type=("payment_type", "first"),  # first = payment_sequential 1
        max_installments=("payment_installments", "max"),
    )
    items = t["order_items"].groupby("order_id", as_index=False).agg(
        n_items=("order_item_id", "count"),
        item_revenue=("price", "sum"),
        freight=("freight_value", "sum"),
    )
    rev = t["reviews"][["order_id", "review_score"]].drop_duplicates("order_id")

    facts = orders.merge(
        t["customers"][["customer_id", "customer_unique_id", "customer_state", "customer_city"]],
        on="customer_id",
        how="left",
    )
    facts = facts.merge(pay, on="order_id", how="left")
    facts = facts.merge(items, on="order_id", how="left")
    facts = facts.merge(rev, on="order_id", how="left")

    facts["delay_days"] = (
        facts["order_delivered_customer_date"] - facts["order_estimated_delivery_date"]
    ).dt.days
    facts["is_late"] = facts["delay_days"] > 0
    facts["order_month"] = facts["order_purchase_timestamp"].dt.to_period("M").astype(str)
    return facts


def build_item_facts(data_dir: Path | str = DATA_DIR) -> pd.DataFrame:
    """One row per order line item with English category name and order month."""
    t = load_all(data_dir)
    items = t["items"] if "items" in t else t["order_items"]
    items = items.merge(
        t["products"][["product_id", "product_category_name"]], on="product_id", how="left"
    )
    items = items.merge(t["category_translation"], on="product_category_name", how="left")
    items["category_en"] = items["product_category_name_english"].fillna(
        items["product_category_name"]
    )
    items = items.merge(
        t["orders"][["order_id", "order_purchase_timestamp", "order_status"]],
        on="order_id",
        how="left",
    )
    items["order_month"] = pd.to_datetime(
        items["order_purchase_timestamp"], errors="coerce"
    ).dt.to_period("M").astype(str)
    return items


def build_rfm(data_dir: Path | str = DATA_DIR) -> pd.DataFrame:
    """RFM table per customer (customer_unique_id) over delivered orders.

    Recency is measured in days vs the latest purchase in the data.
    Scores are 1-5 quintiles (rank-based, so ties can't break the binning).
    """
    facts = build_order_facts(data_dir)
    delivered = facts[facts["order_status"] == "delivered"].copy()
    max_date = delivered["order_purchase_timestamp"].max()

    rfm = delivered.groupby("customer_unique_id", as_index=False).agg(
        last_purchase=("order_purchase_timestamp", "max"),
        frequency=("order_id", "nunique"),
        monetary=("total_payment", "sum"),
        customer_state=("customer_state", "first"),
    )
    rfm["recency_days"] = (max_date - rfm["last_purchase"]).dt.days

    rfm["r_score"] = pd.qcut(
        rfm["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    rfm["f_score"] = pd.qcut(
        rfm["frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["m_score"] = pd.qcut(
        rfm["monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["rfm_score"] = (
        rfm["r_score"].astype(str) + rfm["f_score"].astype(str) + rfm["m_score"].astype(str)
    )
    rfm["segment"] = rfm.apply(
        lambda r: assign_segment(r["r_score"], r["f_score"], r["m_score"]), axis=1
    )
    return rfm


def assign_segment(r: int, f: int, m: int) -> str:
    """Business-friendly RFM segment labels."""
    if r >= 4 and f >= 4:
        return "Champions"
    if r >= 4 and f >= 2:
        return "Loyal Customers"
    if r >= 3 and f >= 3:
        return "Potential Loyalists"
    if r >= 4:
        return "New Customers"
    if r == 3:
        return "Need Attention"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f >= 2:
        return "Hibernating"
    return "Lost"
