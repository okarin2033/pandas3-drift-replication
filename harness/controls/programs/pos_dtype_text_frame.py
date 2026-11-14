# VERIFY control pos_dtype_text_frame (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: DTYPE_DRIFT.
# dtype_significant card, text columns change dtype (object -> str)
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["name", "city", "plan"]]
