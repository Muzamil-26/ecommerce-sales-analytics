-- ============================================================================
-- 10_customer_cohort_retention.sql
-- Business question: Do customers acquired in a given month come back?
-- Cohort = month of first delivered order; retention measured at +1/+2/+3
-- months using window-friendly month arithmetic.
-- ============================================================================

WITH first_orders AS (
    SELECT
        c.customer_unique_id,
        MIN(strftime('%Y-%m', o.order_purchase_timestamp)) AS cohort_month
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
    GROUP BY 1
),
activity AS (
    SELECT DISTINCT
        c.customer_unique_id,
        strftime('%Y-%m', o.order_purchase_timestamp) AS active_month
    FROM orders o
    JOIN customers c ON c.customer_id = o.customer_id
    WHERE o.order_status = 'delivered'
),
months_diff AS (
    SELECT
        f.cohort_month,
        f.customer_unique_id,
        (CAST(substr(a.active_month, 1, 4) AS INT) * 12
         + CAST(substr(a.active_month, 6, 2) AS INT))
        - (CAST(substr(f.cohort_month, 1, 4) AS INT) * 12
         + CAST(substr(f.cohort_month, 6, 2) AS INT)) AS month_offset
    FROM first_orders f
    JOIN activity a ON a.customer_unique_id = f.customer_unique_id
)
SELECT
    cohort_month,
    COUNT(DISTINCT customer_unique_id) AS cohort_size,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN month_offset = 1
                                     THEN customer_unique_id END)
                / COUNT(DISTINCT customer_unique_id), 1) AS retained_m1_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN month_offset = 2
                                     THEN customer_unique_id END)
                / COUNT(DISTINCT customer_unique_id), 1) AS retained_m2_pct,
    ROUND(100.0 * COUNT(DISTINCT CASE WHEN month_offset = 3
                                     THEN customer_unique_id END)
                / COUNT(DISTINCT customer_unique_id), 1) AS retained_m3_pct
FROM months_diff
GROUP BY cohort_month
HAVING cohort_size >= 100
ORDER BY cohort_month;
