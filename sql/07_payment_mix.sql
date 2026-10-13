-- ============================================================================
-- 07_payment_mix.sql
-- Business question: How do customers pay? How common are instalment plans?
-- (An order's payment type is taken from its first payment row, matching the
-- Python analysis in src/ecommerce.py.)
-- ============================================================================

WITH order_pay AS (
    SELECT
        order_id,
        SUM(payment_value)        AS total,
        MAX(payment_installments) AS installments
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
    COUNT(*) AS orders,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_of_orders_pct,
    ROUND(SUM(op.total), 2) AS revenue,
    ROUND(AVG(op.installments), 1) AS avg_installments
FROM orders o
JOIN order_pay op     ON op.order_id = o.order_id
JOIN first_payment fp ON fp.order_id = o.order_id
WHERE o.order_status = 'delivered'
GROUP BY fp.payment_type
ORDER BY orders DESC;

-- Instalment behaviour on credit cards specifically
SELECT
    p.payment_installments AS installments,
    COUNT(*) AS orders,
    ROUND(AVG(p.payment_value), 2) AS avg_ticket
FROM payments p
JOIN orders o ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
  AND p.payment_type = 'credit_card'
GROUP BY 1
ORDER BY 1;
