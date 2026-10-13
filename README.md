# 🛒 E-commerce Sales Analytics

[![Python](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQL-SQLite-003B57)](https://www.sqlite.org/)
[![pandas](https://img.shields.io/badge/pandas-3.0-150458)](https://pandas.pydata.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9-F7931E)](https://scikit-learn.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.65-FF4B4B)](https://streamlit.io/)

End-to-end data analysis of a Brazilian online marketplace: **99,441 orders, R$ 15.4M revenue** —
from raw multi-table data → SQL analysis → Python EDA & RFM segmentation → an interactive
deployed dashboard.

## Problem statement

An e-commerce marketplace wants to know: *what drives revenue, why do customers leave bad
reviews, and which customers are worth fighting to keep?* This project answers that with
real data — revenue trends, category and geography deep-dives, a delivery-vs-satisfaction
analysis, payment behaviour, and an RFM customer segmentation with concrete next steps.

## Dataset

**Olist Brazilian E-commerce** (public, CC BY-NC-SA 4.0) — orders placed **2016-09-04 → 2018-10-17**
across 8 relational tables: customers, orders, order items, payments, reviews, products,
sellers, category translations. Committed CSVs in `data/` are analysis-ready copies
(~59MB); see `data/data_dictionary.md` for every column and the two documented size trims.

### Live demo data

The deployed dashboard runs on a documented **0.5% seeded sample** (`data_sample/`,
~0.35MB, ~500 orders) so it stays fast on free hosting. The sample is a seeded
random draw of `order_id`s (seed 42) with `order_items`, `payments` and `reviews`
filtered to those orders, and `customers`/`products`/`sellers` filtered to the IDs
actually referenced by the sampled rows — so referential integrity is preserved
and every chart and filter behaves exactly as on the full data. Reproduce it with
`python scripts/build_sample.py`. The full `data/` tables are what the SQL
analysis and notebooks ran on — **every figure reported below comes from the full
dataset**, not the sample.

## Key findings

Every number below is computed from the data (see `notebooks/` and `sql/`):

| # | Finding |
|---|---|
| 1 | **R$ 15.42M revenue** from 96,478 delivered orders (97% of 99,441); **AOV R$ 159.85**; avg review **4.16★** |
| 2 | **Nov 2017 was the peak month** — R$ 1.15M, +53.6% MoM (Black Friday effect); revenue grew ~10x from Jan 2017 (R$ 128k) to early 2018 (~R$ 1.1M/month) |
| 3 | **Top categories:** health & beauty (R$ 1.23M), watches & gifts (R$ 1.17M), bed/bath/table (R$ 1.02M) — but the top 3 are only 26% of revenue, so the catalogue is diversified |
| 4 | **Geography is concentrated:** São Paulo alone drives **37% of revenue** (R$ 5.77M); SP + RJ + MG = 63% |
| 5 | **Only 3.0% of customers ever buy again** — an acquisition-driven marketplace, not a retention business. Repeat buyers are worth ~1.9x (R$ 309 vs R$ 161 lifetime value) |
| 6 | **Delivery is the #1 satisfaction lever:** 6.8% of orders arrive late (avg 10.6 days late). Late orders average **2.27★ vs 4.29★** on time; **54% of late orders get 1 star** (vs 7% on time) |
| 7 | **Payments:** 77% credit card (avg 3.5 instalments — instalment culture is real), 20% boleto (cash-based) |
| 8 | **RFM segmentation:** the **At Risk** segment (22,357 customers, 24% of revenue = R$ 3.7M) is the biggest lever — valuable customers going quiet. Champions (14,871) drive 17% of revenue |

## Recommendations

1. **Fix late deliveries first** — worst categories: audio (11.6% late), home & comfort (9.3%), office furniture (8.0%). Every late order risks a 1-star review; tightening SLAs on these categories directly protects the 4.16★ average.
2. **Launch a win-back program for the At Risk segment** — R$ 3.7M of revenue from customers who bought often but went quiet. Personalised offers in categories they already bought.
3. **Attack the 3% repeat rate** — post-purchase onboarding for New Customers (7,479 recent one-time buyers); converting even a fraction to a second purchase nearly doubles their lifetime value.
4. **Double down on SP/RJ/MG logistics** — 63% of revenue; faster fulfilment there compounds both revenue and reviews.

## Tech stack

- **SQL (SQLite)** — 10 analytical queries: CTEs, window functions (`LAG`, `NTILE`, `RANK`), cohort retention
- **Python (pandas, scikit-learn)** — EDA, RFM segmentation, KMeans validation
- **Streamlit + Plotly** — interactive dashboard (filters, KPIs, segment explorer)
- No BI tools involved — everything is code, version-controlled and reproducible

## Project structure

```
├── streamlit_app.py          # interactive dashboard (deploys to Streamlit Cloud)
├── requirements.txt          # pinned dependencies
├── src/ecommerce.py          # shared loading/cleaning/RFM module (used by notebooks + app)
├── sql/
│   ├── 00_schema.sql         # table definitions
│   ├── 01_..._10_*.sql       # 10 business analyses (trends, categories, RFM, cohorts…)
│   └── load_into_sqlite.sh   # builds ecommerce.db and runs every query
├── notebooks/
│   ├── 01_eda.ipynb          # revenue, categories, geography, delivery vs reviews, payments
│   └── 02_customer_segmentation.ipynb  # RFM + KMeans validation + segment playbook
├── scripts/
│   ├── prepare_data.py       # raw download -> committed data/*.csv
│   ├── compute_findings.py   # reproduces every headline number
│   └── build_notebooks.py    # generates the .ipynb files
├── data/
│   ├── data_dictionary.md    # every table/column + derived definitions
│   └── *.csv                 # full 59MB analysis tables — not in this repo (too large);
│                             # reproduce: put the 8 raw Olist CSVs in data/raw/ and run
│                             # python scripts/prepare_data.py (raw: "Olist Brazilian
│                             # E-Commerce Public Dataset" on Kaggle)
└── data_sample/              # 0.5% seeded sample (~0.35MB) — powers the live demo dashboard
```

## Run it locally

```bash
# 1. dashboard
pip install -r requirements.txt
streamlit run streamlit_app.py

# 2. SQL (needs sqlite3)
bash sql/load_into_sqlite.sh        # builds ecommerce.db, runs all 10 queries

# 3. notebooks
pip install jupyter
jupyter notebook notebooks/
```

To reproduce `data/` from the raw download: place the 8 Olist CSVs in `data/raw/` and run
`python scripts/prepare_data.py`.

## Interview talking points

- *"I picked a real multi-table dataset over a toy CSV because joins are where analysts spend
  their time — the SQL folder has a monthly-revenue query with MoM growth via `LAG`, an RFM
  segmentation with `NTILE`, and a cohort-retention analysis."*
- *"The headline insight: late deliveries average 2.27 stars vs 4.29 on time — so I traced the
  worst late rates to specific categories (audio at 11.6%) to give logistics a target list."*
- *"Only 3% of customers repeat, so I segmented with RFM and found the At Risk segment holds
  R$ 3.7M of revenue — that's the win-back campaign I'd run first."*
- *"Everything is reproducible: one shared Python module feeds the notebooks and the dashboard,
  and a script rebuilds the SQLite database and re-runs all queries."*
