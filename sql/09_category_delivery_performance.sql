-- ============================================================================
-- 09_category_delivery_performance.sql
-- Business question: Which product categories suffer the worst delivery
-- performance? Late deliveries destroy review scores (see query 06), so this
-- tells logistics exactly where to focus.
-- ============================================================================

WITH item_delivery AS (
    SELECT
        COALESCE(t.product_category_name_english, pr.product_category_name) AS category,
        o.order_id,
        CAST(julianday(o.order_delivered_customer_date)
            - julianday(o.order_estimated_delivery_date) AS INTEGER) AS delay_days
    FROM order_items i
    JOIN products pr ON pr.product_id = i.product_id
    LEFT JOIN category_translation t
           ON t.product_category_name = pr.product_category_name
    JOIN orders o ON o.order_id = i.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
)
SELECT
    category,
    COUNT(DISTINCT order_id) AS orders,
    ROUND(100.0 * SUM(CASE WHEN delay_days > 0 THEN 1 ELSE 0 END)
                / COUNT(*), 1) AS late_rate_pct,
    ROUND(AVG(delay_days), 1)  AS avg_delay_days
FROM item_delivery
GROUP BY category
HAVING COUNT(DISTINCT order_id) >= 200   -- ignore tiny categories
ORDER BY late_rate_pct DESC
LIMIT 15;
