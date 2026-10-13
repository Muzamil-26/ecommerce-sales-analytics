-- ============================================================================
-- 00_schema.sql — table definitions for the Olist e-commerce dataset (SQLite)
-- Load order: run this first, then import each CSV with:
--   .mode csv
--   .import --skip 1 data/<file>.csv <table>
-- (or use sql/load_into_sqlite.sh which does it all for you)
-- ============================================================================

DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS sellers;
DROP TABLE IF EXISTS category_translation;

CREATE TABLE customers (
    customer_id            TEXT PRIMARY KEY,
    customer_unique_id     TEXT NOT NULL,
    customer_zip_code_prefix TEXT,
    customer_city          TEXT,
    customer_state         TEXT
);

CREATE TABLE orders (
    order_id                    TEXT PRIMARY KEY,
    customer_id                 TEXT NOT NULL REFERENCES customers(customer_id),
    order_status                TEXT NOT NULL,
    order_purchase_timestamp    TEXT,
    order_approved_at           TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT
);

CREATE TABLE order_items (
    order_id      TEXT NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id    TEXT,
    seller_id     TEXT,
    price         REAL,
    freight_value REAL,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE payments (
    order_id             TEXT NOT NULL,
    payment_sequential   INTEGER NOT NULL,
    payment_type         TEXT,
    payment_installments INTEGER,
    payment_value        REAL,
    PRIMARY KEY (order_id, payment_sequential)
);

CREATE TABLE reviews (
    -- NOTE: review_id is NOT unique in the raw Olist data (789 ids appear
    -- twice, a known quirk of the public dataset), so there is no PK here.
    review_id             TEXT,
    order_id              TEXT NOT NULL,
    review_score          INTEGER CHECK (review_score BETWEEN 1 AND 5),
    review_creation_date  TEXT,
    review_answer_timestamp TEXT
);

CREATE TABLE products (
    product_id              TEXT PRIMARY KEY,
    product_category_name   TEXT,
    product_name_lenght     INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty      INTEGER,
    product_weight_g        REAL,
    product_length_cm       REAL,
    product_height_cm       REAL,
    product_width_cm        REAL
);

CREATE TABLE sellers (
    seller_id             TEXT PRIMARY KEY,
    seller_zip_code_prefix TEXT,
    seller_city           TEXT,
    seller_state          TEXT
);

CREATE TABLE category_translation (
    product_category_name         TEXT PRIMARY KEY,
    product_category_name_english TEXT
);
