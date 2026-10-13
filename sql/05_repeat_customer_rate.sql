-- ============================================================================
-- 05_repeat_customer_rate.sql
-- Business question: What share of customers buy more than once? Is this a
-- repeat-purchase business or a one-and-done marketplace?
-- (customer_unique_id identifies the real person across guest checkouts)
-- ============================================================================

WITH customer_orders AS (
    SELECT
        c.customer_unique_id,
        COUNT(DISTINCT o.order_id) AS n_orders,
        SUM(p.payment_value)       AS lifetime_value
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN payments p  ON p.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
)
SELECT
    COUNT(*) AS customers,
    SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) AS repeat_customers,
    ROUND(100.0 * SUM(CASE WHEN n_orders > 1 THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS repeat_rate_pct,
    ROUND(AVG(lifetime_value), 2) AS avg_lifetime_value,
    ROUND(AVG(CASE WHEN n_orders > 1 THEN lifetime_value END), 2)
        AS avg_ltv_repeat_customers,
    ROUND(AVG(CASE WHEN n_orders = 1 THEN lifetime_value END), 2)
        AS avg_ltv_one_time_customers
FROM customer_orders;
