# M_QF3_14 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("gauges.csv")
acc, last = {}, None
for site, r in zip(df["site"].tolist(), df["reading"].tolist()):
    if not pd.isna(r):
        last = float(r)
    acc.setdefault(site.strip().lower(), [])
    if last is not None:
        acc[site.strip().lower()].append(last)
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 3) for k in keys], index=pd.Index(keys))
