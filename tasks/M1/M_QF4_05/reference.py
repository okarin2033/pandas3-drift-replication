# M_QF4_05 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import statistics
import pandas as pd

df = pd.read_csv("subscribers.csv")
acc = {}
for t, f in zip(df["tier"].tolist(), df["monthly_fee"].tolist()):
    if not pd.isna(f):
        acc.setdefault(t.strip().lower(), []).append(float(f))
keys = sorted(acc)
result = pd.DataFrame({"mean": [round(statistics.fmean(acc[k]), 3) for k in keys],
                       "std": [round(statistics.stdev(acc[k]), 3) for k in keys]},
                      index=pd.Index(keys))
