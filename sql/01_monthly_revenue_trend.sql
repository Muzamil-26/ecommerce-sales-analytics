-- ============================================================================
-- 01_monthly_revenue_trend.sql
-- Business question: How has revenue trended over time? Which was the best
-- month, and how strong was month-over-month growth?
-- Revenue = sum of payment_value on delivered orders.
-- ============================================================================

WITH monthly AS (
    SELECT
        strftime('%Y-%m', o.order_purchase_timestamp) AS order_month,
        SUM(p.payment_value)                         AS revenue,
        COUNT(DISTINCT o.order_id)                    AS orders
    FROM orders o
    JOIN payments p ON p.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
)
SELECT
    order_month,
    ROUND(revenue, 2)                                   AS revenue,
    orders,
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
                / LAG(revenue) OVER (ORDER BY order_month), 1) AS mom_growth_pct
FROM monthly
ORDER BY order_month;
