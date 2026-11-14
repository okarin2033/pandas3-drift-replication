# M_QF1_14 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": "category"})
df["sales"] = df["sales"].fillna(0)
result = df.pivot_table(index="week", columns="branch_code", values="sales", aggfunc="sum", fill_value=0, observed=False)
