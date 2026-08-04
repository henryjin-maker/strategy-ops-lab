from pathlib import Path

import numpy as np
import pandas as pd


RANDOM_SEED = 42
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

rng = np.random.default_rng(RANDOM_SEED)
DATA_DIR.mkdir(exist_ok=True)


def generate_users(n_users: int = 2000) -> pd.DataFrame:
    user_ids = np.arange(1, n_users + 1)

    users = pd.DataFrame(
        {
            "user_id": user_ids,
            "register_date": pd.to_datetime(
                rng.choice(
                    pd.date_range("2025-01-01", "2025-06-30"),
                    size=n_users,
                )
            ),
            "channel": rng.choice(
                ["自然流量", "短视频投放", "达人推荐", "站内活动"],
                size=n_users,
                p=[0.35, 0.25, 0.20, 0.20],
            ),
            "city_level": rng.choice(
                ["一线", "新一线", "二线", "三线及以下"],
                size=n_users,
                p=[0.15, 0.25, 0.30, 0.30],
            ),
        }
    )

    return users


def generate_orders(users: pd.DataFrame, n_orders: int = 7000) -> pd.DataFrame:
    order_users = rng.choice(users["user_id"], size=n_orders)
    order_dates = pd.to_datetime(
        rng.choice(pd.date_range("2025-07-01", "2025-09-30"), size=n_orders)
    )

    orders = pd.DataFrame(
        {
            "order_id": np.arange(1, n_orders + 1),
            "user_id": order_users,
            "order_date": order_dates,
            "category": rng.choice(
                ["服饰", "美妆", "食品", "数码", "家居"],
                size=n_orders,
            ),
            "gmv": np.round(rng.lognormal(mean=4.1, sigma=0.55, size=n_orders), 2),
            "discount": np.round(
                rng.choice([0, 5, 10, 20, 30], size=n_orders, p=[0.35, 0.20, 0.20, 0.15, 0.10]),
                2,
            ),
            "is_first_order": rng.choice(
                [0, 1],
                size=n_orders,
                p=[0.72, 0.28],
            ),
        }
    )

    orders["net_gmv"] = np.round(orders["gmv"] - orders["discount"], 2)
    orders["net_gmv"] = orders["net_gmv"].clip(lower=1)

    return orders


def generate_content_events(
    users: pd.DataFrame, n_events: int = 30000
) -> pd.DataFrame:
    event_users = rng.choice(users["user_id"], size=n_events)

    events = pd.DataFrame(
        {
            "event_id": np.arange(1, n_events + 1),
            "user_id": event_users,
            "event_date": pd.to_datetime(
                rng.choice(pd.date_range("2025-07-01", "2025-09-30"), size=n_events)
            ),
            "content_type": rng.choice(
                ["短视频", "直播", "图文"],
                size=n_events,
                p=[0.50, 0.30, 0.20],
            ),
            "event_type": rng.choice(
                ["曝光", "点击", "加购", "分享"],
                size=n_events,
                p=[0.68, 0.18, 0.08, 0.06],
            ),
        }
    )

    return events


def main() -> None:
    users = generate_users()
    orders = generate_orders(users)
    events = generate_content_events(users)

    users.to_csv(DATA_DIR / "users.csv", index=False)
    orders.to_csv(DATA_DIR / "orders.csv", index=False)
    events.to_csv(DATA_DIR / "content_events.csv", index=False)

    print(f"已生成 {len(users):,} 条用户数据")
    print(f"已生成 {len(orders):,} 条订单数据")
    print(f"已生成 {len(events):,} 条内容行为数据")
    print(f"文件保存位置：{DATA_DIR}")


if __name__ == "__main__":
    main()