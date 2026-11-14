# M_QF1_03 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
counts = {}
for v in df["home_city"].tolist():
    if isinstance(v, str) and v.strip() != "-":
        k = v.strip().title()
        counts[k] = counts.get(k, 0) + 1
keys = sorted(counts)
result = pd.Series([counts[k] for k in keys], index=pd.Index(keys), dtype="int64")
