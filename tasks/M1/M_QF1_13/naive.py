# M_QF1_13 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": str})
missing = df["sales"].astype(str).str.strip().isin(["", "nan", "NaN", "None"])
result = df[missing].groupby("branch_code").size()
