# VERIFY control ord_concat_dates (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_ONLY.
# concat(axis=1, sort=False) of date-indexed frames: index sorted on 2.3.3, first appearance on 3.x
import pandas as pd
a = pd.read_csv("left.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "left"})
b = pd.read_csv("right.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "right"})
result = pd.concat([a, b], axis=1, sort=False)
