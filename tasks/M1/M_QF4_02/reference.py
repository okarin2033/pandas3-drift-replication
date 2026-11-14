# M_QF4_02 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("unit_sales.csv")
regions, channels = ["north", "south", "west"], ["online", "store", "kiosk"]
tot = {(r, c): 0.0 for r in regions for c in channels}
for r, c, u in zip(df["region"].tolist(), df["channel"].tolist(), df["units"].tolist()):
    if not pd.isna(u):
        tot[(r, c)] += float(u)
idx = pd.MultiIndex.from_tuples([(r, c) for r in regions for c in channels])
result = pd.DataFrame({"units": [tot[k] for k in idx]}, index=idx)
