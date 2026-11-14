# M_QF3_11 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
known, allv = {}, {}
for w, c in zip(df["ward"].tolist(), df["charge"].tolist()):
    k = w.strip().lower()
    known.setdefault(k, [])
    allv.setdefault(k, [])
    if pd.isna(c):
        allv[k].append(0.0)
    else:
        known[k].append(float(c))
        allv[k].append(float(c))
keys = sorted(allv)
result = pd.DataFrame({"mean_known": [round(sum(known[k]) / len(known[k]), 2) for k in keys],
                       "mean_zero_filled": [round(sum(allv[k]) / len(allv[k]), 2) for k in keys]},
                      index=pd.Index(keys))
