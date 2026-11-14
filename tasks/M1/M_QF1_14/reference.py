# M_QF1_14 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": str})
weeks = sorted(set(int(w) for w in df["week"].tolist()))
codes = sorted(set(df["branch_code"].tolist()))
cell = {}
for w, c, s in zip(df["week"].tolist(), df["branch_code"].tolist(), df["sales"].tolist()):
    cell[(int(w), c)] = cell.get((int(w), c), 0.0) + (0.0 if pd.isna(s) else float(s))
data = {c: [cell.get((w, c), 0.0) for w in weeks] for c in codes}
out = pd.DataFrame(data, index=pd.Index(weeks), columns=codes)
out.columns.name = "branch_code"
result = out
