# M_QF4_04 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import math
import pandas as pd

df = pd.read_csv("purchases.csv")
acc = {}
for c, s in zip(df["store_city"].tolist(), df["spend"].tolist()):
    if isinstance(c, str):
        acc.setdefault(c.strip().title(), []).append(float(s))
keys = sorted(acc)
result = pd.DataFrame({"store_city": keys, "spend": [round(math.fsum(acc[k]), 2) for k in keys]})
