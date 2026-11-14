# REPAIR control dtsig_value_counts_series (hand-written, synthetic data; 2026-11-11, review MF5). Expected class: DTYPE_ONLY.
# dtype_significant card; distinct counts (int64 on both sides), only the dtype of the text index changes: not DTYPE_DRIFT
import pandas as pd
df = pd.read_csv("people.csv")
result = df["city"].value_counts()
