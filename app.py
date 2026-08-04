from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parent
DB_PATH = PROJECT_DIR / "data" / "strategy_ops.db"


st.set_page_config(
    page_title="用户增长策略分析平台",
    page_icon="📊",
    layout="wide",
)

st.title("内容电商用户增长策略分析平台")
st.caption("用于评估不同获客渠道的用户质量、交易贡献与运营机会")


@st.cache_data
def load_channel_metrics() -> pd.DataFrame:
    query = """
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
    """

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)


metrics = load_channel_metrics()

total_users = int(metrics["user_count"].sum())
total_gmv = metrics["total_gmv"].sum()
total_orders = int(metrics["order_count"].sum())
overall_pay_rate = metrics["paying_users"].sum() / total_users

col1, col2, col3, col4 = st.columns(4)

col1.metric("用户数", f"{total_users:,}")
col2.metric("GMV", f"¥{total_gmv:,.0f}")
col3.metric("订单数", f"{total_orders:,}")
col4.metric("整体付费率", f"{overall_pay_rate:.1%}")

st.divider()

left_col, right_col = st.columns(2)

with left_col:
    st.subheader("各渠道 GMV")
    gmv_chart = px.bar(
        metrics,
        x="channel",
        y="total_gmv",
        text_auto=".0f",
        labels={"channel": "渠道", "total_gmv": "GMV"},
    )
    st.plotly_chart(gmv_chart, use_container_width=True)

with right_col:
    st.subheader("各渠道用户质量")
    quality_chart = px.scatter(
        metrics,
        x="pay_rate",
        y="avg_order_value",
        size="user_count",
        color="channel",
        text="channel",
        labels={
            "pay_rate": "付费率",
            "avg_order_value": "客单价",
            "user_count": "用户数",
        },
    )
    quality_chart.update_traces(textposition="top center")
    st.plotly_chart(quality_chart, use_container_width=True)

st.subheader("渠道经营明细")

display_metrics = metrics.copy()
display_metrics["total_gmv"] = display_metrics["total_gmv"].map(
    lambda value: f"¥{value:,.2f}"
)
display_metrics["avg_order_value"] = display_metrics["avg_order_value"].map(
    lambda value: f"¥{value:,.2f}"
)
display_metrics["pay_rate"] = display_metrics["pay_rate"].map(
    lambda value: f"{value:.1%}"
)

st.dataframe(display_metrics, use_container_width=True, hide_index=True)

st.info(
    "策略提示：自然流量贡献最高 GMV；达人推荐用户规模较小，但付费率和客单价较高，"
    "可以进一步评估扩大优质达人投放的可行性。"
)
st.divider()

st.header("用户分层分析")

@st.cache_data
def load_rfm_metrics() -> pd.DataFrame:
    query = """
    WITH user_rfm AS (
        SELECT
            u.user_id,
            MAX(o.order_date) AS last_order_date,
            COUNT(o.order_id) AS frequency,
            ROUND(SUM(o.net_gmv), 2) AS monetary,
            CAST(
                julianday('2025-10-01') - julianday(MAX(o.order_date))
                AS INTEGER
            ) AS recency
        FROM users AS u
        JOIN orders AS o
            ON u.user_id = o.user_id
        GROUP BY u.user_id
    ),
    scored_users AS (
        SELECT
            *,
            NTILE(4) OVER (ORDER BY recency DESC) AS recency_score,
            NTILE(4) OVER (ORDER BY frequency ASC) AS frequency_score,
            NTILE(4) OVER (ORDER BY monetary ASC) AS monetary_score
        FROM user_rfm
    )
    SELECT
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
        END AS user_segment,
        COUNT(*) AS user_count,
        ROUND(AVG(recency), 1) AS avg_recency,
        ROUND(AVG(frequency), 2) AS avg_frequency,
        ROUND(AVG(monetary), 2) AS avg_monetary
    FROM scored_users
    GROUP BY user_segment
    ORDER BY user_count DESC;
    """

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)


rfm_metrics = load_rfm_metrics()

st.dataframe(rfm_metrics, use_container_width=True, hide_index=True)

segment_chart = px.bar(
    rfm_metrics,
    x="user_segment",
    y="user_count",
    color="user_segment",
    text_auto=True,
    labels={
        "user_segment": "用户分层",
        "user_count": "用户数",
    },
)

st.plotly_chart(segment_chart, use_container_width=True)
st.divider()

st.header("优惠券 A/B 实验")

@st.cache_data
def load_experiment_metrics() -> pd.DataFrame:
    query = """
    SELECT
        experiment_group,
        COUNT(*) AS user_count,
        SUM(converted) AS converted_users,
        ROUND(
            CAST(SUM(converted) AS FLOAT) / COUNT(*),
            4
        ) AS conversion_rate,
        ROUND(SUM(coupon_cost), 2) AS coupon_cost,
        ROUND(SUM(net_revenue), 2) AS net_revenue,
        ROUND(
            SUM(net_revenue) / COUNT(*),
            2
        ) AS revenue_per_user
    FROM coupon_experiment
    GROUP BY experiment_group
    ORDER BY experiment_group DESC;
    """

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)


experiment_metrics = load_experiment_metrics()

treatment_rate = experiment_metrics.loc[
    experiment_metrics["experiment_group"] == "实验组",
    "conversion_rate",
].iloc[0]

control_rate = experiment_metrics.loc[
    experiment_metrics["experiment_group"] == "对照组",
    "conversion_rate",
].iloc[0]

conversion_lift = treatment_rate / control_rate - 1

metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric(
    "实验组转化率",
    f"{treatment_rate:.1%}",
)

metric_col2.metric(
    "对照组转化率",
    f"{control_rate:.1%}",
)

metric_col3.metric(
    "相对转化提升",
    f"{conversion_lift:.1%}",
)

st.dataframe(
    experiment_metrics,
    use_container_width=True,
    hide_index=True,
)

experiment_chart = px.bar(
    experiment_metrics,
    x="experiment_group",
    y="revenue_per_user",
    color="experiment_group",
    text_auto=".2f",
    labels={
        "experiment_group": "实验分组",
        "revenue_per_user": "人均净收入",
    },
)

st.plotly_chart(experiment_chart, use_container_width=True)

st.success(
    f"策略结论：实验组转化率提升 {conversion_lift:.1%}。"
    "在扣除优惠成本后，仍需结合人均净收入判断是否值得推广。"
)
st.divider()

st.header("用户分层运营策略")

strategy_table = pd.DataFrame(
    [
        {
            "用户分层": "高价值用户",
            "核心问题": "贡献高，但需要维持长期活跃",
            "运营动作": "会员权益、新品优先、专属内容",
            "补贴策略": "少用普惠券，优先非价格权益",
            "核心指标": "复购率、月活跃率、用户生命周期价值",
        },
        {
            "用户分层": "潜力用户",
            "核心问题": "已有购买行为，但价值尚未充分释放",
            "运营动作": "组合推荐、跨品类推荐、成长任务",
            "补贴策略": "设置满减门槛，推动客单价提升",
            "核心指标": "二次购买率、客单价、品类扩展率",
        },
        {
            "用户分层": "流失风险用户",
            "核心问题": "历史购买频率较高，但近期未购买",
            "运营动作": "限时召回、个性化 Push、内容再触达",
            "补贴策略": "定向召回券，设置有效期",
            "核心指标": "召回率、召回后 30 日复购率",
        },
        {
            "用户分层": "沉睡用户",
            "核心问题": "活跃度和购买频率都较低",
            "运营动作": "低成本批量触达、热门内容推荐",
            "补贴策略": "低面额券，严格控制预算",
            "核心指标": "唤醒率、单用户触达成本",
        },
        {
            "用户分层": "一般用户",
            "核心问题": "当前消费贡献较低",
            "运营动作": "自动化内容推荐和轻量活动",
            "补贴策略": "仅在关键节点发放优惠",
            "核心指标": "转化率、订单频次",
        },
    ]
)

st.dataframe(
    strategy_table,
    use_container_width=True,
    hide_index=True,
)
