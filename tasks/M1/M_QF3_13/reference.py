# M_QF3_13 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("gauges.csv")
acc = {}
for site, r, lv in zip(df["site"].tolist(), df["reading"].tolist(), df["level"].tolist()):
    k = site.strip().lower()
    acc.setdefault(k, [])
    if not pd.isna(r) and int(lv) <= 60:
        acc[k].append(float(r))
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 3) for k in keys], index=pd.Index(keys))
