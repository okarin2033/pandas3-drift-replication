# M_QF3_07 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
acc = {}
for w, s in zip(df["ward"].tolist(), df["stay_days"].tolist()):
    k = w.strip().lower()
    if pd.isna(s):
        acc.setdefault(k, [])
        continue
    acc.setdefault(k, []).append(min(float(s), 14.0))
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 2) for k in keys], index=pd.Index(keys))
