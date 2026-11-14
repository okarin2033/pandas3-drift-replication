# VERIFY control dt_groupby_sum (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: DTYPE_ONLY.
# group keys end up in an object (2.3.3) or str (3.x) index; sums equal
import pandas as pd
df = pd.read_csv("people.csv")
result = df.groupby("city")["amount"].sum()
