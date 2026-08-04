.headers on
.mode column

SELECT
    CASE
        WHEN discount = 0 THEN '未使用优惠'
        ELSE '使用优惠'
    END AS subsidy_group,
    COUNT(*) AS order_count,
    COUNT(DISTINCT user_id) AS user_count,
    ROUND(SUM(gmv), 2) AS original_gmv,
    ROUND(SUM(discount), 2) AS subsidy_cost,
    ROUND(SUM(net_gmv), 2) AS net_gmv,
    ROUND(AVG(net_gmv), 2) AS avg_net_gmv,
    ROUND(
        SUM(discount) / NULLIF(SUM(gmv), 0),
        4
    ) AS subsidy_rate
FROM orders
GROUP BY subsidy_group
ORDER BY net_gmv DESC;
