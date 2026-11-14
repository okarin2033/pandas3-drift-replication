# M_QF1_04 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": str})
tot = {}
for code, s in zip(df["branch_code"].tolist(), df["sales"].tolist()):
    tot[code] = tot.get(code, 0.0) + (0.0 if pd.isna(s) else float(s))
keys = sorted(tot)
result = pd.Series([tot[k] for k in keys], index=pd.Index(keys), dtype="float64")
