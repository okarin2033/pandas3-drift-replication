# M_QF1_13 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": str})
counts = {}
for code, sales in zip(df["branch_code"].tolist(), df["sales"].tolist()):
    if pd.isna(sales):
        counts[code] = counts.get(code, 0) + 1
keys = sorted(counts)
result = pd.Series([counts[k] for k in keys], index=pd.Index(keys), dtype="int64")
