# Data Dictionary

Source: **Olist Brazilian E-commerce** public dataset (CC BY-NC-SA 4.0), obtained via a
Hugging Face mirror of the original Kaggle release. 99,441 orders placed 2016-09-04 → 2018-10-17.

Committed files are analysis-ready copies produced by `scripts/prepare_data.py` from the raw
download in `data/raw/` (gitignored). Two size trims were applied to stay under the ~60MB
free-hosting limit — both documented below; every analytical column is intact.

## Tables

### `customers.csv` — 99,441 rows
| column | meaning |
|---|---|
| `customer_id` | per-order customer key (PK). One `customer_unique_id` may map to several `customer_id`s (guest checkouts) |
| `customer_unique_id` | identifies the real person across orders — use this for customer counts |
| `customer_zip_code_prefix` | 5-digit zip prefix |
| `customer_city` | city |
| `customer_state` | 2-letter Brazilian state |

### `orders.csv` — 99,441 rows
| column | meaning |
|---|---|
| `order_id` | PK |
| `customer_id` | → customers |
| `order_status` | `delivered` (97%), `shipped`, `canceled`, `invoiced`, `processing`, `unavailable`, `created`, `approved` |
| `order_purchase_timestamp` | when the order was placed |
| `order_approved_at` | payment approval time |
| `order_delivered_carrier_date` | handed to the carrier |
| `order_delivered_customer_date` | actually received by the customer |
| `order_estimated_delivery_date` | promised delivery date |

### `order_items.csv` — 112,650 rows (dropped: `shipping_limit_date`, an internal seller deadline unused by any analysis)
| column | meaning |
|---|---|
| `order_id`, `order_item_id` | composite PK — one row per line item |
| `product_id` | → products |
| `seller_id` | → sellers |
| `price` | item price in R$ (excludes freight) |
| `freight_value` | shipping cost in R$ |

### `payments.csv` — 103,886 rows
| column | meaning |
|---|---|
| `order_id`, `payment_sequential` | composite PK — an order can be split across payment rows |
| `payment_type` | `credit_card`, `boleto` (cash voucher), `voucher`, `debit_card` |
| `payment_installments` | number of instalments (0 appears twice — raw quirk) |
| `payment_value` | amount in R$ |

### `reviews.csv` — 99,224 rows (dropped: `review_comment_title`, `review_comment_message` — Portuguese free text, unused)
| column | meaning |
|---|---|
| `review_id` | **not unique** in the raw data (789 ids duplicated — known Olist quirk) |
| `order_id` | → orders |
| `review_score` | 1–5 stars |
| `review_creation_date` | when the review form was sent |
| `review_answer_timestamp` | when the customer answered |

### `products.csv` — 32,951 rows
| column | meaning |
|---|---|
| `product_id` | PK |
| `product_category_name` | Portuguese category → join `category_translation.csv` for English |
| `product_name_lenght`, `product_description_lenght` | character counts (note the source's `lenght` typo, kept as-is) |
| `product_photos_qty` | number of product photos |
| `product_weight_g`, `product_length_cm`, `product_height_cm`, `product_width_cm` | dimensions |

### `sellers.csv` — 3,095 rows
| column | meaning |
|---|---|
| `seller_id` | PK |
| `seller_zip_code_prefix`, `seller_city`, `seller_state` | seller location |

### `category_translation.csv` — 70 rows
Portuguese → English product category names.

## Derived definitions (used consistently in SQL, notebooks and dashboard)

- **Revenue** = `SUM(payment_value)` over **delivered** orders only.
- **AOV** = revenue ÷ delivered orders.
- **delay_days** = `order_delivered_customer_date − order_estimated_delivery_date`, truncated to whole
  days; **late** = delay_days > 0 (i.e. at least one full day past the promised date).
- **Repeat customer** = `customer_unique_id` with more than one delivered order.
- **RFM** (see `02_customer_segmentation.ipynb`): per `customer_unique_id` over delivered orders;
  recency in days vs the latest purchase in the data; 1–5 quintile scores; business segments
  (Champions, Loyal Customers, Potential Loyalists, New Customers, Need Attention, At Risk,
  Hibernating, Lost).
