# MECH_A confirm program C05 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): astype(..., copy=False), write into the new object, then use the original.
import pandas as pd

df = pd.read_csv("measures.csv")
b = df.astype({"reading": "float64"}, copy=False)
b.iloc[0, 1] = 0.0
result = df
