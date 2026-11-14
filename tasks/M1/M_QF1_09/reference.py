# M_QF1_09 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv", dtype={"fee": str})
counts = {}
for f in df["fee"].tolist():
    counts[f] = counts.get(f, 0) + 1
keys = sorted(counts, key=float)
result = pd.Series([counts[k] for k in keys], index=pd.Index(keys), dtype="int64")
