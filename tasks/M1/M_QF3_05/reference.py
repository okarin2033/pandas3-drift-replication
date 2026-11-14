# M_QF3_05 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("gauges.csv")
raw, cln = {}, {}
for site, r, lv in zip(df["site"].tolist(), df["reading"].tolist(), df["level"].tolist()):
    k = site.strip().lower()
    raw.setdefault(k, [])
    cln.setdefault(k, [])
    if pd.isna(r):
        continue
    raw[k].append(float(r))
    if int(lv) <= 60:
        cln[k].append(float(r))
keys = sorted(raw)
result = pd.DataFrame({"raw_mean": [round(sum(raw[k]) / len(raw[k]), 3) for k in keys],
                       "clean_mean": [round(sum(cln[k]) / len(cln[k]), 3) for k in keys]},
                      index=pd.Index(keys))
