from pathlib import Path
import sqlite3

import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "strategy_ops.db"


def main() -> None:
    users = pd.read_csv(DATA_DIR / "users.csv")
    orders = pd.read_csv(DATA_DIR / "orders.csv")
    events = pd.read_csv(DATA_DIR / "content_events.csv")

    with sqlite3.connect(DB_PATH) as conn:
        users.to_sql("users", conn, if_exists="replace", index=False)
        orders.to_sql("orders", conn, if_exists="replace", index=False)
        events.to_sql("content_events", conn, if_exists="replace", index=False)

    print(f"数据库已创建：{DB_PATH}")
    print(f"users 表：{len(users):,} 行")
    print(f"orders 表：{len(orders):,} 行")
    print(f"content_events 表：{len(events):,} 行")


if __name__ == "__main__":
    main()