.headers on
.mode column

WITH group_metrics AS (
    SELECT
        experiment_group,
        COUNT(*) AS user_count,
        SUM(converted) AS converted_users,
        ROUND(
            CAST(SUM(converted) AS FLOAT) / COUNT(*),
            4
        ) AS conversion_rate,
        ROUND(SUM(order_value), 2) AS gross_revenue,
        ROUND(SUM(coupon_cost), 2) AS coupon_cost,
        ROUND(SUM(net_revenue), 2) AS net_revenue
    FROM coupon_experiment
    GROUP BY experiment_group
),

experiment_result AS (
    SELECT
        MAX(
            CASE
                WHEN experiment_group = '实验组'
                THEN conversion_rate
            END
        ) AS treatment_rate,
        MAX(
            CASE
                WHEN experiment_group = '对照组'
                THEN conversion_rate
            END
        ) AS control_rate,
        MAX(
            CASE
                WHEN experiment_group = '实验组'
                THEN net_revenue
            END
        ) AS treatment_revenue,
        MAX(
            CASE
                WHEN experiment_group = '对照组'
                THEN net_revenue
            END
        ) AS control_revenue
    FROM group_metrics
)

SELECT
    gm.*,
    CASE
        WHEN gm.experiment_group = '实验组'
        THEN ROUND(
            (er.treatment_rate - er.control_rate)
            / er.control_rate,
            4
        )
        ELSE NULL
    END AS relative_conversion_lift
FROM group_metrics AS gm
CROSS JOIN experiment_result AS er;