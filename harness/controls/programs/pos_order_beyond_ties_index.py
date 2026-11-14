# VERIFY control pos_order_beyond_ties_index (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_DRIFT.
# flagged on the (distinct) group labels: any reordering is beyond ties
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["plan", "city"]].value_counts(sort=False)
