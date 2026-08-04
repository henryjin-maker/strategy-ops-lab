.headers on
.mode column

WITH channel_users AS (
    SELECT
        channel,
        COUNT(*) AS user_count
    FROM users
    GROUP BY channel
),

channel_orders AS (
    SELECT
        u.channel,
        COUNT(o.order_id) AS order_count,
        ROUND(SUM(o.net_gmv), 2) AS total_gmv,
        ROUND(AVG(o.net_gmv), 2) AS avg_order_value,
        COUNT(DISTINCT o.user_id) AS paying_users
    FROM users AS u
    LEFT JOIN orders AS o
        ON u.user_id = o.user_id
    GROUP BY u.channel
)

SELECT
    cu.channel,
    cu.user_count,
    co.paying_users,
    co.order_count,
    co.total_gmv,
    co.avg_order_value,
    ROUND(
        CAST(co.paying_users AS FLOAT) / cu.user_count,
        4
    ) AS pay_rate
FROM channel_users AS cu
JOIN channel_orders AS co
    ON cu.channel = co.channel
ORDER BY co.total_gmv DESC;
