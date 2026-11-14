# M_QF4_16 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
acc = {}
for y, f in zip(df["joined_year"].tolist(), df["monthly_fee"].tolist()):
    k = int(y) // 5 * 5
    acc.setdefault(k, [])
    if not pd.isna(f):
        acc[k].append(float(f))
keys = sorted(acc)
result = pd.DataFrame({"period_start": keys, "mean_fee": [round(sum(acc[k]) / len(acc[k]), 2) for k in keys]})
result["period_start"] = result["period_start"].astype("int64")
