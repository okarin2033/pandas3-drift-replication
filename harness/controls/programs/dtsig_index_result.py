# REPAIR control dtsig_index_result (hand-written, synthetic data; 2026-11-11, review MF5). Expected class: DTYPE_DRIFT.
# dtype_significant card; the result is an Index of text labels, so its dtype is the dtype of its values (object -> str): DTYPE_DRIFT
import pandas as pd
df = pd.read_csv("people.csv")
result = df.columns
