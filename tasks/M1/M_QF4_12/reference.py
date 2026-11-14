# M_QF4_12 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("purchases.csv")
cnt = {}
for c in df["store_city"].tolist():
    if isinstance(c, str):
        k = c.strip().title()
        cnt[k] = cnt.get(k, 0) + 1
result = [f"{k}: {cnt[k]} purchases" for k in sorted(cnt)]
