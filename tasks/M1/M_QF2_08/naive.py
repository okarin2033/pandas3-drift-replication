# M_QF2_08 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("shipments.csv", parse_dates=["ordered_on", "shipped_on"])
base = pd.Timestamp("2025-01-01")
for c in df.select_dtypes(include="datetime64[ns]").columns:
    df[c] = (df[c] - base).dt.days
result = df
