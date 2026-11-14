# M_QF4_08 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("unit_sales.csv")
regions, channels = ["north", "south", "west"], ["online", "store", "kiosk"]
flag = {(r, c): False for r in regions for c in channels}
for r, c, u in zip(df["region"].tolist(), df["channel"].tolist(), df["units"].tolist()):
    if not pd.isna(u) and float(u) > 50:
        flag[(r, c)] = True
idx = pd.MultiIndex.from_tuples([(r, c) for r in regions for c in channels])
result = pd.Series([flag[k] for k in idx], index=idx, dtype="bool")
