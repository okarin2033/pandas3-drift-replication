# VERIFY control dt_to_dict_keys (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: IDENTICAL.
# a plain dict of Python strings and floats cannot differ by dtype: IDENTICAL (guards against calling every program DTYPE_ONLY)
import pandas as pd
df = pd.read_csv("people.csv")
result = df.groupby("city")["amount"].sum().to_dict()
