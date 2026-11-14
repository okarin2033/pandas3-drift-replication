# VERIFY control dt_value_counts_series (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: DTYPE_ONLY.
# distinct counts, so order is fixed; only the index dtype differs
import pandas as pd
df = pd.read_csv("people.csv")
result = df["city"].value_counts()
