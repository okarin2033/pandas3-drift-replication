# MECH_A confirm program D08 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): select_dtypes(include="datetime64[ns]") after parse_dates, then format the selected columns.
import pandas as pd

df = pd.read_csv("orders.csv", parse_dates=["order_date", "ship_date"])
date_cols = df.select_dtypes(include="datetime64[ns]").columns
for c in date_cols:
    df[c] = df[c].dt.strftime("%Y-%m")
result = df
