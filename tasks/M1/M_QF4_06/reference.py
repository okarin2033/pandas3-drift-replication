# M_QF4_06 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import math
import pandas as pd

df = pd.read_csv("subscribers.csv")
acc = {}
for t, f in zip(df["tier"].tolist(), df["monthly_fee"].tolist()):
    acc.setdefault(t.strip().lower(), [])
    if not pd.isna(f):
        acc[t.strip().lower()].append(float(f))
result = {k: round(math.fsum(acc[k]), 2) for k in sorted(acc)}
