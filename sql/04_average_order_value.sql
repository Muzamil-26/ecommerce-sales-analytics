-- ============================================================================
-- 04_average_order_value.sql
-- Business question: What is the average order value (AOV), and how does it
-- vary by payment type?
-- ============================================================================

-- Overall AOV (delivered orders)
SELECT
    COUNT(DISTINCT o.order_id)                                     AS delivered_orders,
    ROUND(SUM(p.payment_value), 2)                                AS total_revenue,
    ROUND(SUM(p.payment_value) / COUNT(DISTINCT o.order_id), 2)    AS avg_order_value
FROM orders o
JOIN payments p ON p.order_id = o.order_id
WHERE o.order_status = 'delivered';

-- AOV by payment type (type taken from the first payment row of each order)
WITH order_total AS (
    SELECT order_id, SUM(payment_value) AS total
    FROM payments
    GROUP BY order_id
),
first_payment AS (
    SELECT order_id, payment_type
    FROM payments
    WHERE payment_sequential = 1
)
SELECT
    fp.payment_type,
    COUNT(*)                    AS orders,
    ROUND(AVG(ot.total), 2)     AS avg_order_value
FROM orders o
JOIN order_total ot   ON ot.order_id = o.order_id
JOIN first_payment fp ON fp.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY fp.payment_type
ORDER BY avg_order_value DESC;
