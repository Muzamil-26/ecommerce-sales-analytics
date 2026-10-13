-- ============================================================================
-- 06_delivery_vs_reviews.sql
-- Business question: Do late deliveries hurt review scores? How big is the
-- gap, and how many orders arrive late?
-- delay_days = actual delivery date - estimated delivery date (> 0 = late)
-- ============================================================================

WITH delivery AS (
    SELECT
        o.order_id,
        CAST(julianday(o.order_delivered_customer_date)
            - julianday(o.order_estimated_delivery_date) AS INTEGER) AS delay_days,
        r.review_score
    FROM orders o
    LEFT JOIN reviews r ON r.order_id = o.order_id
    WHERE o.order_status = 'delivered'
      AND o.order_delivered_customer_date IS NOT NULL
      AND o.order_estimated_delivery_date IS NOT NULL
),
bucketed AS (
    SELECT
        CASE
            WHEN delay_days <= 0 THEN 'on time / early'
            WHEN delay_days <= 7 THEN '1-7 days late'
            ELSE '8+ days late'
        END AS delivery_bucket,
        review_score
    FROM delivery
)
SELECT
    delivery_bucket,
    COUNT(*) AS orders,
    ROUND(AVG(review_score), 2) AS avg_review_score,
    ROUND(100.0 * SUM(CASE WHEN review_score = 5 THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS pct_5_star,
    ROUND(100.0 * SUM(CASE WHEN review_score = 1 THEN 1 ELSE 0 END) / COUNT(*), 1)
        AS pct_1_star
FROM bucketed
WHERE review_score IS NOT NULL
GROUP BY 1
ORDER BY avg_review_score DESC;

-- Headline late-delivery rate
SELECT
    COUNT(*) AS delivered_orders,
    SUM(CASE WHEN CAST(julianday(order_delivered_customer_date)
                  - julianday(order_estimated_delivery_date) AS INTEGER) > 0
             THEN 1 ELSE 0 END) AS late_orders,
    ROUND(100.0 * SUM(CASE WHEN CAST(julianday(order_delivered_customer_date)
                                - julianday(order_estimated_delivery_date) AS INTEGER) > 0
                           THEN 1 ELSE 0 END) / COUNT(*), 1) AS late_rate_pct,
    ROUND(AVG(CASE WHEN CAST(julianday(order_delivered_customer_date)
                        - julianday(order_estimated_delivery_date) AS INTEGER) > 0
                   THEN CAST(julianday(order_delivered_customer_date)
                        - julianday(order_estimated_delivery_date) AS INTEGER) END), 1)
        AS avg_days_late_when_late
FROM orders
WHERE order_status = 'delivered'
  AND order_delivered_customer_date IS NOT NULL
  AND order_estimated_delivery_date IS NOT NULL;
