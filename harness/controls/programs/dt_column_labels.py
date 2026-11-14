# VERIFY control dt_column_labels (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: DTYPE_ONLY.
# result is the Index of column labels: object on 2.3.3, str on 3.x; labels equal
import pandas as pd
df = pd.read_csv("people.csv")
result = df.columns
