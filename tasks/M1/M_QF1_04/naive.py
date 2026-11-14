# M_QF1_04 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": "category"})
result = df.groupby("branch_code", observed=True)["sales"].sum()
