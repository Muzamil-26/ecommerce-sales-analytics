-- ============================================================================
-- 02_top_categories.sql
-- Business question: Which product categories drive revenue? Where should
-- marketing and inventory focus?
-- ============================================================================

SELECT
    COALESCE(t.product_category_name_english, pr.product_category_name) AS category,
    COUNT(DISTINCT i.order_id)   AS orders,
    SUM(i.price)                 AS revenue,
    ROUND(AVG(i.price), 2)       AS avg_item_price,
    ROUND(100.0 * SUM(i.price) / SUM(SUM(i.price)) OVER (), 1) AS revenue_share_pct
FROM order_items i
JOIN products pr        ON pr.product_id = i.product_id
LEFT JOIN category_translation t
       ON t.product_category_name = pr.product_category_name
JOIN orders o           ON o.order_id = i.order_id
                       AND o.order_status = 'delivered'
GROUP BY 1
ORDER BY revenue DESC
LIMIT 10;
