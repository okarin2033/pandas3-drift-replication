# M_QF3_08 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
acc = {}
for w, c in zip(df["ward"].tolist(), df["charge"].tolist()):
    acc.setdefault(w.strip().lower(), []).append(0.0 if pd.isna(c) else float(c))
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 2) for k in keys], index=pd.Index(keys))
