# MECH_A confirm program C01 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): chained assignment df[col][mask] = v, then use df.
import pandas as pd

df = pd.read_csv("orders.csv")
df["amount"][df["status"] == "cancelled"] = 0
result = df
