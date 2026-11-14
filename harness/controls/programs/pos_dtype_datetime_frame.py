# VERIFY control pos_dtype_datetime_frame (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: DTYPE_DRIFT.
# dtype_significant card, datetime unit changes
import pandas as pd
df = pd.read_csv("people.csv", parse_dates=["signup"])
result = df[["id", "signup"]]
