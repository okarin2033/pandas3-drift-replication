# VERIFY control dt_pivot_table (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: DTYPE_ONLY.
# row and column labels are text; dtype of the label indexes differs, values equal
import pandas as pd
df = pd.read_csv("people.csv")
result = pd.pivot_table(df, index="city", columns="plan", values="amount", aggfunc="sum", fill_value=0)
