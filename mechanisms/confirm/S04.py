# MECH_A confirm program S04 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): NumPy semantics on Series.values of a text column (np.where on values == "shipped").
import numpy as np
import pandas as pd

df = pd.read_csv("orders.csv")
df["is_shipped"] = np.where(df["status"].values == "shipped", 1, 0)
result = df.groupby("region")["is_shipped"].sum()
