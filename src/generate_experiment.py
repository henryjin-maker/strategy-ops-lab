from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


RANDOM_SEED = 2026
rng = np.random.default_rng(RANDOM_SEED)

PROJECT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_DIR / "data"
DB_PATH = DATA_DIR / "strategy_ops.db"


def main() -> None:
    users = pd.read_csv(DATA_DIR / "users.csv")

    experiment = users[["user_id", "channel"]].copy()

    experiment["experiment_group"] = rng.choice(
        ["实验组", "对照组"],
        size=len(experiment),
        p=[0.5, 0.5],
    )

    experiment["received_coupon"] = (
        experiment["experiment_group"] == "实验组"
    ).astype(int)

    conversion_probability = np.where(
        experiment["experiment_group"] == "实验组",
        0.14,
        0.11,
    )

    experiment["converted"] = (
        rng.random(len(experiment)) < conversion_probability
    ).astype(int)

    order_value = np.round(
        rng.lognormal(mean=4.2, sigma=0.45, size=len(experiment)),
        2,
    )

    experiment["order_value"] = np.where(
        experiment["converted"] == 1,
        order_value,
        0,
    )

    experiment["coupon_cost"] = np.where(
        (experiment["received_coupon"] == 1)
        & (experiment["converted"] == 1),
        10,
        0,
    )

    experiment["net_revenue"] = (
        experiment["order_value"] - experiment["coupon_cost"]
    ).round(2)

    experiment.to_csv(DATA_DIR / "coupon_experiment.csv", index=False)

    with sqlite3.connect(DB_PATH) as conn:
        experiment.to_sql(
            "coupon_experiment",
            conn,
            if_exists="replace",
            index=False,
        )

    print("优惠券实验数据生成成功")
    print(experiment["experiment_group"].value_counts())
    print(f"总样本量：{len(experiment):,}")
    print(f"数据已写入：{DB_PATH}")


if __name__ == "__main__":
    main()
    