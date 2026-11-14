# VERIFY control ord_and_dtype_unflagged (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_ONLY.
# order and index dtype both change; unflagged -> not drift (ORDER_ONLY; DTYPE_ONLY would also be non-drift)
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["plan", "city"]].value_counts(sort=False)
