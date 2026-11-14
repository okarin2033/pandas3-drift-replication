# MECH_A confirm program L01 (LOUD_CONTEXT). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): resample with the old month alias "M".
import pandas as pd

df = pd.read_csv("sales.csv", parse_dates=["sale_date"])
result = df.set_index("sale_date")["amount"].resample("M").sum()
