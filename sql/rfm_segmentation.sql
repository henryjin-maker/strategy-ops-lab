.headers on
.mode column

WITH user_rfm AS (
    SELECT
        u.user_id,
        u.channel,
        MAX(o.order_date) AS last_order_date,
        COUNT(o.order_id) AS frequency,
        ROUND(SUM(o.net_gmv), 2) AS monetary,
        CAST(
            julianday('2025-10-01') - julianday(MAX(o.order_date))
            AS INTEGER
        ) AS recency
    FROM users AS u
    LEFT JOIN orders AS o
        ON u.user_id = o.user_id
    GROUP BY
        u.user_id,
        u.channel
),

scored_users AS (
    SELECT
        *,
        NTILE(4) OVER (
            ORDER BY recency DESC
        ) AS recency_score,
        NTILE(4) OVER (
            ORDER BY frequency ASC
        ) AS frequency_score,
        NTILE(4) OVER (
            ORDER BY monetary ASC
        ) AS monetary_score
    FROM user_rfm
    WHERE frequency > 0
),

segmented_users AS (
    SELECT
        *,
        CASE
            WHEN recency_score >= 3
                 AND frequency_score >= 3
                 AND monetary_score >= 3
                THEN '高价值用户'
            WHEN recency_score >= 3
                 AND frequency_score >= 2
                THEN '潜力用户'
            WHEN recency_score <= 2
                 AND frequency_score >= 3
                THEN '流失风险用户'
            WHEN recency_score <= 2
                 AND frequency_score <= 2
                THEN '沉睡用户'
            ELSE '一般用户'
        END AS user_segment
    FROM scored_users
)

SELECT
    user_segment,
    COUNT(*) AS user_count,
    ROUND(AVG(recency), 1) AS avg_recency,
    ROUND(AVG(frequency), 2) AS avg_frequency,
    ROUND(AVG(monetary), 2) AS avg_monetary
FROM segmented_users
GROUP BY user_segment
ORDER BY user_count DESC;