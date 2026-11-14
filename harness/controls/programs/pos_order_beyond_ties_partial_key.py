# VERIFY control pos_order_beyond_ties_partial_key (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_DRIFT.
# same data as tie_partial_ties_frame but the frame is not sorted by n: the n column itself changes order (3,2,2,2,2,1 vs 2,2,2,2,1,3), so the change is beyond ties of the key
import pandas as pd
df = pd.read_csv("people2.csv")
result = df[["city"]].value_counts(sort=False).reset_index(name="n")
