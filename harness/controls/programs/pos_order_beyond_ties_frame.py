# VERIFY control pos_order_beyond_ties_frame (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_DRIFT.
# flagged on city; the same frame lists the groups in a different order, cities all distinct per row
import pandas as pd
df = pd.read_csv("people2.csv")
result = df[["city"]].value_counts(sort=False).reset_index(name="n")
