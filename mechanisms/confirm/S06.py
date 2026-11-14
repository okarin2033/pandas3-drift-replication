# MECH_A confirm program S06 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): read a column of zero-padded codes as category, then total per code.
import pandas as pd

df = pd.read_csv("shops.csv", dtype={"shop_code": "category"})
result = df.groupby("shop_code", observed=True)["sales"].sum()
