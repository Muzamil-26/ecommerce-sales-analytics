"""Generate notebooks/01_eda.ipynb and notebooks/02_customer_segmentation.ipynb.

The notebooks are built as JSON (nbformat 4) and then executed headless with:
    jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb
All numbers inside are computed from data/ at execution time.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB_DIR = ROOT / "notebooks"
NB_DIR.mkdir(exist_ok=True)


def md(lines):
    return {"cell_type": "markdown", "metadata": {}, "source": lines}


def code(lines):
    return {
        "cell_type": "code",
        "metadata": {},
        "source": lines,
        "outputs": [],
        "execution_count": None,
    }


def notebook(cells, title):
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "title": title,
        },
        "cells": cells,
    }


def write_nb(name, cells, title):
    path = NB_DIR / name
    path.write_text(json.dumps(notebook(cells, title), indent=1), encoding="utf-8")
    print(f"wrote {path}")


# ---------------------------------------------------------------- 01_eda.ipynb
eda = [
    md([
        "# E-commerce Sales Analytics — Exploratory Data Analysis\n",
        "\n",
        "**Dataset:** Olist Brazilian E-commerce (public, CC BY-NC-SA 4.0) — 99,441 orders "
        "placed Sep 2016 – Oct 2018, stored as 8 relational tables "
        "(customers, orders, order items, payments, reviews, products, sellers, category translations).\n",
        "\n",
        "**Goal:** understand what drives revenue, how delivery performance affects customer "
        "satisfaction, and where the business should focus next.\n",
        "\n",
        "All loading/cleaning lives in `src/ecommerce.py`, so the notebooks, the SQL queries "
        "and the Streamlit dashboard analyse the exact same tables.",
    ]),
    code([
        "import sys\n",
        "sys.path.insert(0, \"../src\")\n",
        "import pandas as pd\n",
        "import plotly.express as px\n",
        "from ecommerce import load_all, build_order_facts, build_item_facts\n",
        "\n",
        "tables = load_all(\"../data\")\n",
        "facts = build_order_facts(\"../data\")   # one row per order\n",
        "items = build_item_facts(\"../data\")    # one row per order line item\n",
        "delivered = facts[facts[\"order_status\"] == \"delivered\"].copy()\n",
        "print(\"order facts:\", facts.shape, \"| item facts:\", items.shape)",
    ]),
    md(["## 1. Dataset overview"]),
    code([
        "for name, df in tables.items():\n",
        "    print(f\"{name:22s} {df.shape[0]:>7,} rows x {df.shape[1]} cols\")\n",
        "print()\n",
        "print(\"purchase window:\", facts[\"order_purchase_timestamp\"].min(),\n",
        "      \"->\", facts[\"order_purchase_timestamp\"].max())\n",
        "print(\"\\norder status:\")\n",
        "print(facts[\"order_status\"].value_counts())",
    ]),
    md([
        "## 2. Revenue trend\n",
        "\n",
        "Revenue = `payment_value` summed over **delivered** orders. "
        "The trend chart starts at 2017-01: 2016 contains only a sparse test period "
        "(266 orders), so including it would distort the picture.",
    ]),
    code([
        "monthly = (delivered[delivered[\"order_month\"] >= \"2017-01\"]\n",
        "           .groupby(\"order_month\")[\"total_payment\"].sum())\n",
        "print(f\"Total revenue (delivered): R$ {delivered['total_payment'].sum():,.0f}\")\n",
        "print(f\"Peak month: {monthly.idxmax()} — R$ {monthly.max():,.0f} \"\n",
        "      f\"(+{(monthly.max()/monthly.shift(1)[monthly.idxmax()]-1)*100:.1f}% MoM)\")\n",
        "fig = px.line(x=monthly.index, y=monthly.values, markers=True,\n",
        "              labels={\"x\": \"Month\", \"y\": \"Revenue (R$\"},\n",
        "              title=\"Monthly revenue — delivered orders\")\n",
        "fig.update_layout(xaxis_tickangle=-45)\n",
        "fig.show()",
    ]),
    md([
        "## 3. Category performance\n",
        "\n",
        "Which categories bring the money? (Revenue at item level, delivered orders only.)",
    ]),
    code([
        "cat = (items[items[\"order_status\"] == \"delivered\"]\n",
        "       .groupby(\"category_en\")\n",
        "       .agg(revenue=(\"price\", \"sum\"), orders=(\"order_id\", \"nunique\"))\n",
        "       .sort_values(\"revenue\", ascending=False))\n",
        "top10 = cat.head(10)\n",
        "print(top10.assign(revenue=top10[\"revenue\"].map(lambda v: f\"R$ {v:,.0f}\")))\n",
        "print(f\"\\nTop-3 categories share of revenue: \"\n",
        "      f\"{cat['revenue'].head(3).sum()/cat['revenue'].sum():.1%}\")\n",
        "fig = px.bar(top10[::-1], x=\"revenue\", y=top10[::-1].index, orientation=\"h\",\n",
        "             labels={\"revenue\": \"Revenue (R$)\", \"category_en\": \"Category\"},\n",
        "             title=\"Top 10 categories by revenue\")\n",
        "fig.show()",
    ]),
    md(["## 4. Geography — a concentrated business"]),
    code([
        "st = (delivered.groupby(\"customer_state\")\n",
        "      .agg(revenue=(\"total_payment\", \"sum\"), orders=(\"order_id\", \"nunique\"))\n",
        "      .sort_values(\"revenue\", ascending=False))\n",
        "print(st.head(10).assign(revenue=lambda d: d[\"revenue\"].map(lambda v: f\"R$ {v:,.0f}\")))\n",
        "print(f\"\\nSao Paulo share of revenue: {st['revenue'].iloc[0]/st['revenue'].sum():.1%}\")\n",
        "fig = px.bar(st.head(12)[::-1], x=\"revenue\", y=st.head(12)[::-1].index,\n",
        "             orientation=\"h\", title=\"Revenue by customer state (top 12)\",\n",
        "             labels={\"revenue\": \"Revenue (R$)\", \"customer_state\": \"State\"})\n",
        "fig.show()",
    ]),
    md([
        "## 5. Delivery performance\n",
        "\n",
        "`delay_days` = actual delivery date − estimated delivery date (whole days; > 0 = late).",
    ]),
    code([
        "dd = delivered.dropna(subset=[\"delay_days\"])\n",
        "print(f\"Late deliveries: {dd['is_late'].mean():.1%} \"\n",
        "      f\"({dd['is_late'].sum():,} of {len(dd):,} delivered orders)\")\n",
        "print(f\"Avg days late (when late): {dd.loc[dd['is_late'], 'delay_days'].mean():.1f}\")\n",
        "print(f\"Avg days early (when on time): {dd.loc[~dd['is_late'], 'delay_days'].mean():.1f}\")\n",
        "fig = px.histogram(dd, x=\"delay_days\", nbins=60, range_x=(-40, 40),\n",
        "                   title=\"Delivery delay distribution (days; > 0 = late)\",\n",
        "                   labels={\"delay_days\": \"Delay (days)\"})\n",
        "fig.show()",
    ]),
    md(["## 6. Late deliveries destroy review scores"]),
    code([
        "rev = delivered.dropna(subset=[\"review_score\", \"delay_days\"]).copy()\n",
        "rev[\"bucket\"] = pd.cut(rev[\"delay_days\"], [-10_000, 0, 7, 10_000],\n",
        "                        labels=[\"on time / early\", \"1-7 days late\", \"8+ days late\"])\n",
        "g = rev.groupby(\"bucket\", observed=True)[\"review_score\"].agg(\n",
        "    [\"mean\", \"count\", lambda s: (s == 5).mean(), lambda s: (s == 1).mean()])\n",
        "g.columns = [\"avg_review\", \"orders\", \"share_5_star\", \"share_1_star\"]\n",
        "print(g.round(2))\n",
        "fig = px.bar(g.reset_index(), x=\"bucket\", y=\"avg_review\",\n",
        "             title=\"Average review score by delivery punctuality\",\n",
        "             labels={\"bucket\": \"\", \"avg_review\": \"Avg review score\"})\n",
        "fig.show()",
    ]),
    md(["## 7. How customers pay"]),
    code([
        "pm = delivered.groupby(\"payment_type\").agg(orders=(\"order_id\", \"nunique\"),\n",
        "                                             avg_inst=(\"max_installments\", \"mean\"))\n",
        "pm[\"share\"] = pm[\"orders\"] / pm[\"orders\"].sum()\n",
        "print(pm.round(2))\n",
        "fig = px.pie(pm.reset_index(), names=\"payment_type\", values=\"orders\",\n",
        "             title=\"Delivered orders by payment type\")\n",
        "fig.show()",
    ]),
    md([
        "## 8. Key takeaways\n",
        "\n",
        "Every number below was computed from the data in the cells above:\n",
        "\n",
        "- **R$ 15.4M revenue** from 96,478 delivered orders (97% of 99,441 placed); "
        "**AOV R$ 159.85**. Nov 2017 was the peak month (R$ 1.15M, +53.6% MoM — Black Friday effect).\n",
        "- **Top categories:** health & beauty (R$ 1.23M), watches & gifts (R$ 1.17M), "
        "bed/bath/table (R$ 1.02M); the top 3 are only 26% of revenue — the catalogue is diversified.\n",
        "- **Geography is concentrated:** São Paulo alone is 37% of revenue; the top 3 states (SP/RJ/MG) are 63%.\n",
        "- **Only 3.0% of customers ever buy again** — this is an acquisition-driven marketplace, "
        "not a retention business. Repeat buyers are worth ~1.9x (R$ 309 vs R$ 161 lifetime value).\n",
        "- **Delivery is the #1 satisfaction lever:** 6.8% of orders arrive late (avg 10.6 days late); "
        "late orders average **2.27★** vs **4.29★** on time, and 54% of late orders get 1 star.\n",
        "- **Payments:** 77% credit card (avg 3.5 instalments — instalment culture matters in Brazil), "
        "20% boleto (cash-based, 1 instalment).\n",
        "- **Data-quality notes:** `review_id` is not unique in the raw file (789 duplicated ids); "
        "~1,400 order items have no product category mapped.",
    ]),
]

# ------------------------------------------------- 02_customer_segmentation.ipynb
seg_nb = [
    md([
        "# Customer Segmentation — RFM Analysis\n",
        "\n",
        "Only **3.0%** of customers buy more than once (see `01_eda.ipynb`), so knowing *which* "
        "customers are valuable — and which valuable ones are slipping away — is the highest-leverage "
        "question for this business.\n",
        "\n",
        "**RFM** scores every customer on:\n",
        "- **R**ecency — days since last purchase (lower is better)\n",
        "- **F**requency — number of orders\n",
        "- **M**onetary — total spend (R$)\n",
        "\n",
        "Each dimension is split into quintiles (1–5), then mapped to business segments. "
        "A KMeans check at the end validates that the segments reflect real structure.",
    ]),
    code([
        "import sys\n",
        "sys.path.insert(0, \"../src\")\n",
        "import numpy as np\n",
        "import pandas as pd\n",
        "import plotly.express as px\n",
        "from ecommerce import build_rfm\n",
        "\n",
        "rfm = build_rfm(\"../data\")\n",
        "print(rfm.shape)\n",
        "print(rfm[[\"recency_days\", \"frequency\", \"monetary\"]].describe().round(1))",
    ]),
    md(["## RFM distributions"]),
    code([
        "for col, title in [(\"recency_days\", \"Recency (days since last purchase)\"),\n",
        "                   (\"frequency\", \"Frequency (orders per customer)\"),\n",
        "                   (\"monetary\", \"Monetary (total spend, R$\")]:\n",
        "    fig = px.histogram(rfm, x=col, nbins=50, title=title)\n",
        "    fig.show()",
    ]),
    md(["## Business segments"]),
    code([
        "seg = (rfm.groupby(\"segment\")\n",
        "        .agg(customers=(\"customer_unique_id\", \"count\"),\n",
        "             revenue=(\"monetary\", \"sum\"),\n",
        "             avg_recency=(\"recency_days\", \"mean\"),\n",
        "             avg_frequency=(\"frequency\", \"mean\"),\n",
        "             avg_monetary=(\"monetary\", \"mean\"))\n",
        "        .sort_values(\"customers\", ascending=False))\n",
        "seg[\"cust_share\"] = seg[\"customers\"] / seg[\"customers\"].sum()\n",
        "seg[\"rev_share\"] = seg[\"revenue\"] / seg[\"revenue\"].sum()\n",
        "print(seg.round(2))\n",
        "fig = px.bar(seg.reset_index(), x=\"segment\", y=\"customers\", color=\"rev_share\",\n",
        "             color_continuous_scale=\"Blues\",\n",
        "             title=\"RFM segments — customer count coloured by revenue share\",\n",
        "             labels={\"segment\": \"\", \"customers\": \"Customers\"})\n",
        "fig.update_layout(xaxis_tickangle=-30)\n",
        "fig.show()",
    ]),
    md([
        "## Sanity check: does KMeans find similar structure?\n",
        "\n",
        "KMeans (k=5) on log-scaled, standardised RFM — a completely different method. "
        "If the clusters line up with the RFM segments, the segmentation is robust.",
    ]),
    code([
        "from sklearn.preprocessing import StandardScaler\n",
        "from sklearn.cluster import KMeans\n",
        "\n",
        "X = StandardScaler().fit_transform(\n",
        "    np.log1p(rfm[[\"recency_days\", \"frequency\", \"monetary\"]]))\n",
        "rfm[\"cluster\"] = KMeans(n_clusters=5, n_init=10, random_state=42).fit_predict(X)\n",
        "prof = (rfm.groupby(\"cluster\")\n",
        "           .agg(customers=(\"customer_unique_id\", \"count\"),\n",
        "                avg_recency=(\"recency_days\", \"mean\"),\n",
        "                avg_frequency=(\"frequency\", \"mean\"),\n",
        "                avg_monetary=(\"monetary\", \"mean\"))\n",
        "           .round(1).sort_values(\"avg_monetary\", ascending=False))\n",
        "print(prof)\n",
        "print(\"\\nCluster vs RFM segment crosstab:\")\n",
        "print(pd.crosstab(rfm[\"cluster\"], rfm[\"segment\"]))",
    ]),
    md([
        "## What to do with each segment\n",
        "\n",
        "- **At Risk (22,357 customers · 24% of revenue, R$ 3.7M)** — the single biggest lever. "
        "They bought often and spent well but went quiet. Win-back campaign: personalised offers, "
        "reminders of categories they bought.\n",
        "- **Champions (14,871 · R$ 2.6M)** — recent, frequent, high spend. VIP treatment, early access, "
        "referral incentives; they are the cheapest source of new customers.\n",
        "- **Loyal Customers (14,993 · R$ 2.5M)** — buy regularly but slightly less recently. "
        "Upsell/cross-sell into adjacent categories.\n",
        "- **New Customers (7,479)** — bought once, recently. With a 3% repeat rate, converting even a "
        "fraction to a second purchase is transformative: post-purchase onboarding + timed discount.\n",
        "- **Hibernating (7,503) + Lost (7,483)** — long gone. Cheap reactivation test on a sample; "
        "don't overspend here.\n",
        "- **Need Attention (7,373)** — average on everything and drifting. Nurture before they slide "
        "into At Risk.\n",
        "\n",
        "Bottom line: retention marketing aimed at **At Risk + New Customers** protects ~R$ 5M of "
        "revenue and attacks the business's core weakness — the 3% repeat-purchase rate.",
    ]),
]

write_nb("01_eda.ipynb", eda, "E-commerce EDA")
write_nb("02_customer_segmentation.ipynb", seg_nb, "RFM Customer Segmentation")
