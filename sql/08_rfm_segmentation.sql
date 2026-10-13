-- ============================================================================
-- 08_rfm_segmentation.sql
-- Business question: Who are our best customers, and which valuable segments
-- are slipping away? RFM = Recency / Frequency / Monetary, scored 1-5 with
-- NTILE window functions, then mapped to business segments.
-- ============================================================================

WITH customer_kpis AS (
    SELECT
        c.customer_unique_id,
        MAX(date(o.order_purchase_timestamp)) AS last_order_date,
        COUNT(DISTINCT o.order_id)             AS frequency,
        SUM(p.payment_value)                   AS monetary
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    JOIN payments p  ON p.order_id = o.order_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
),
scored AS (
    SELECT
        customer_unique_id,
        CAST(julianday((SELECT MAX(date(order_purchase_timestamp)) FROM orders))
             - julianday(last_order_date) AS INT) AS recency_days,
        frequency,
        monetary,
        6 - NTILE(5) OVER (ORDER BY julianday(last_order_date) DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency)                            AS f_score,
        NTILE(5) OVER (ORDER BY monetary)                             AS m_score
    FROM customer_kpis
),
segmented AS (
    SELECT *,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 THEN 'Champions'
            WHEN r_score >= 4 AND f_score >= 2 THEN 'Loyal Customers'
            WHEN r_score >= 3 AND f_score >= 3 THEN 'Potential Loyalists'
            WHEN r_score >= 4                 THEN 'New Customers'
            WHEN r_score = 3                  THEN 'Need Attention'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
            WHEN r_score <= 2 AND f_score >= 2 THEN 'Hibernating'
            ELSE 'Lost'
        END AS segment
    FROM scored
)
SELECT
    segment,
    COUNT(*) AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS share_of_customers_pct,
    ROUND(SUM(monetary), 2) AS revenue,
    ROUND(100.0 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1) AS share_of_revenue_pct,
    ROUND(AVG(recency_days), 0) AS avg_recency_days,
    ROUND(AVG(frequency), 1)    AS avg_frequency,
    ROUND(AVG(monetary), 2)     AS avg_monetary
FROM segmented
GROUP BY segment
ORDER BY revenue DESC;
