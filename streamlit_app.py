"""E-commerce Sales Analytics — interactive Streamlit dashboard.

Olist Brazilian marketplace data (Sep 2016 – Oct 2018).
Run locally:  streamlit run streamlit_app.py
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from ecommerce import build_item_facts, build_order_facts, build_rfm  # noqa: E402

st.set_page_config(
    page_title="E-commerce Sales Analytics",
    page_icon="🛒",
    layout="wide",
)

DATA_DIR = Path(__file__).resolve().parent / "data_sample"


@st.cache_data(show_spinner="Loading data…")
def load_data():
    facts = build_order_facts(DATA_DIR)
    items = build_item_facts(DATA_DIR)
    rfm = build_rfm(DATA_DIR)
    return facts, items, rfm


facts, items, rfm = load_data()
delivered_all = facts[facts["order_status"] == "delivered"].copy()

# ------------------------------------------------------------------ sidebar
st.sidebar.header("Filters")
min_date = facts["order_purchase_timestamp"].min().date()
max_date = facts["order_purchase_timestamp"].max().date()
date_range = st.sidebar.slider(
    "Purchase date range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
)
states = sorted(delivered_all["customer_state"].dropna().unique())
sel_states = st.sidebar.multiselect("Customer state", states, default=states)
categories = sorted(items["category_en"].dropna().unique())
sel_cats = st.sidebar.multiselect("Product category", categories, default=categories)

mask = (
    (facts["order_purchase_timestamp"].dt.date >= date_range[0])
    & (facts["order_purchase_timestamp"].dt.date <= date_range[1])
    & (facts["customer_state"].isin(sel_states))
    & (facts["order_status"] == "delivered")
)
f = facts[mask].copy()
fi = items[
    (items["order_id"].isin(f["order_id"]))
    & (items["category_en"].isin(sel_cats))
    & (items["order_status"] == "delivered")
].copy()

st.title("🛒 E-commerce Sales Analytics")
st.caption(
    "Olist Brazilian marketplace · 99,441 orders (Sep 2016 – Oct 2018) · "
    "revenue = payment value on delivered orders"
)

# ------------------------------------------------------------------ KPIs
revenue = f["total_payment"].sum()
orders = f["order_id"].nunique()
aov = revenue / orders if orders else 0
avg_review = f["review_score"].mean()
late_rate = f["is_late"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total revenue", f"R$ {revenue:,.0f}")
c2.metric("Delivered orders", f"{orders:,}")
c3.metric("Avg order value", f"R$ {aov:,.2f}")
c4.metric("Avg review score", f"{avg_review:.2f} ★")
c5.metric("Late deliveries", f"{late_rate:.1%}")

# ------------------------------------------------------------------ row 1
col1, col2 = st.columns(2)
with col1:
    monthly = f.groupby("order_month")["total_payment"].sum().reset_index()
    fig = px.line(
        monthly, x="order_month", y="total_payment", markers=True,
        title="Monthly revenue trend", labels={"order_month": "", "total_payment": "Revenue (R$)"},
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, width="stretch")
with col2:
    cat = (
        fi.groupby("category_en")
        .agg(revenue=("price", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10)
        .reset_index()
    )
    fig = px.bar(
        cat.iloc[::-1], x="revenue", y="category_en", orientation="h",
        title="Top 10 categories by revenue",
        labels={"revenue": "Revenue (R$)", "category_en": ""},
    )
    st.plotly_chart(fig, width="stretch")

# ------------------------------------------------------------------ row 2
col3, col4 = st.columns(2)
with col3:
    rev = f.dropna(subset=["review_score", "delay_days"]).copy()
    rev["delivery"] = rev["is_late"].map({True: "Late", False: "On time / early"})
    g = rev.groupby("delivery")["review_score"].mean().reset_index()
    fig = px.bar(
        g, x="delivery", y="review_score", color="delivery",
        title="Late deliveries destroy review scores",
        labels={"delivery": "", "review_score": "Avg review score"},
        color_discrete_map={"Late": "#e45756", "On time / early": "#54a24b"},
    )
    st.plotly_chart(fig, width="stretch")
with col4:
    pm = f.groupby("payment_type")["order_id"].nunique().reset_index()
    fig = px.pie(pm, names="payment_type", values="order_id",
                 title="Orders by payment type")
    st.plotly_chart(fig, width="stretch")

# ------------------------------------------------------------------ RFM
st.subheader("Customer segmentation (RFM)")
seg = (
    rfm.groupby("segment")
    .agg(customers=("customer_unique_id", "count"), revenue=("monetary", "sum"))
    .reset_index()
    .sort_values("customers", ascending=False)
)
col5, col6 = st.columns([1, 2])
with col5:
    fig = px.pie(seg, names="segment", values="customers",
                 title="Customers per segment", hole=0.4)
    st.plotly_chart(fig, width="stretch")
with col6:
    st.dataframe(
        seg.assign(
            cust_share=(seg["customers"] / seg["customers"].sum()).map("{:.1%}".format),
            rev_share=(seg["revenue"] / seg["revenue"].sum()).map("{:.1%}".format),
            revenue=seg["revenue"].map(lambda v: f"R$ {v:,.0f}"),
        )[["segment", "customers", "cust_share", "revenue", "rev_share"]],
        width="stretch",
        hide_index=True,
    )

# ------------------------------------------------------- segment explorer
st.subheader("Segment explorer")
seg_filter = st.multiselect(
    "Segment", sorted(rfm["segment"].unique()), default=sorted(rfm["segment"].unique())
)
explorer = rfm[rfm["segment"].isin(seg_filter)].copy()
explorer = explorer.sort_values("monetary", ascending=False)
st.dataframe(
    explorer[[
        "customer_unique_id", "segment", "recency_days", "frequency",
        "monetary", "r_score", "f_score", "m_score", "customer_state",
    ]].rename(columns={
        "customer_unique_id": "customer", "recency_days": "recency (days)",
        "frequency": "orders", "monetary": "spend (R$)",
    }).head(500),
    width="stretch",
    hide_index=True,
)
st.download_button(
    "Download segment table (CSV)",
    explorer.to_csv(index=False).encode("utf-8"),
    file_name="rfm_segments.csv",
    mime="text/csv",
)

st.caption(
    "Data: Olist Brazilian E-commerce public dataset (CC BY-NC-SA 4.0), "
    "via Hugging Face mirror. Code: SQL + Python (pandas, scikit-learn) + Streamlit."
)
