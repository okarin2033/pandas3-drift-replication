# VERIFY control flag_dtype_on_order_only (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_ONLY/DTYPE_DRIFT.
# dtype_significant card on a program whose result changes order and index dtype: both ORDER_ONLY and DTYPE_DRIFT are defensible readings; recorded, not scored
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["plan", "city"]].value_counts(sort=False)
