# MECH_A confirm program S04 (attempt 2, written after attempt 1 gave no value drift). drafted_by: pkg:MECH_A, 2026-11-11.
# Idea (catalogue): NumPy semantics on Series.values of a text column; here the NumPy missing-value idiom
# "values != values" on the raw array, counted per region.
import pandas as pd

df = pd.read_csv("orders.csv")
vals = df["status"].values
df["status_missing"] = vals != vals
result = df.groupby("region")["status_missing"].sum()
