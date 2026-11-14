# MECH_A confirm program D03 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): month-end timestamp from to_period("M").dt.end_time used as a group key.
import pandas as pd

df = pd.read_csv("sales.csv")
df["month_end"] = pd.to_datetime(df["sale_date"]).dt.to_period("M").dt.end_time
result = df.groupby("month_end")["amount"].sum()
