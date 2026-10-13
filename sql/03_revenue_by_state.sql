-- ============================================================================
-- 03_revenue_by_state.sql
-- Business question: Which Brazilian states bring the most revenue, and how
-- concentrated is the business geographically?
-- ============================================================================

WITH state_rev AS (
    SELECT
        c.customer_state                        AS state,
        COUNT(DISTINCT o.order_id)               AS orders,
        SUM(p.payment_value)                    AS revenue
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN payments p  ON p.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
)
SELECT
    state,
    orders,
    ROUND(revenue, 2) AS revenue,
    ROUND(revenue / orders, 2) AS avg_order_value,
    ROUND(100.0 * revenue / SUM(revenue) OVER (), 1) AS revenue_share_pct,
    RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM state_rev
ORDER BY revenue DESC;
