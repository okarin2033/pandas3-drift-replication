# VERIFY control tie_partial_ties_frame (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_ONLY.
# one group has count 3, four have count 2, one has count 1: after a stable descending sort the count column is equal at every row, only the cities inside the count-2 block change places
import pandas as pd
df = pd.read_csv("people2.csv")
result = df[["city"]].value_counts(sort=False).sort_values(ascending=False, kind="stable").reset_index(name="n")
