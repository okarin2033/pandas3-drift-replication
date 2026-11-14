# VERIFY control pos_order_concat_dates (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_DRIFT.
# date index in a different order, flagged on the index
import pandas as pd
a = pd.read_csv("left.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "left"})
b = pd.read_csv("right.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "right"})
result = pd.concat([a, b], axis=1, sort=False)
