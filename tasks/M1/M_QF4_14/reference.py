# M_QF4_14 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("unit_sales.csv")
regions, channels = ["north", "south", "west"], ["online", "store", "kiosk"]
cnt = {(r, c): 0 for r in regions for c in channels}
for r, c, u in zip(df["region"].tolist(), df["channel"].tolist(), df["units"].tolist()):
    if pd.isna(u):
        cnt[(r, c)] += 1
keys = [(r, c) for r in regions for c in channels]
result = pd.DataFrame({"region": [k[0] for k in keys], "channel": [k[1] for k in keys],
                       "missing_weeks": [cnt[k] for k in keys]})
result["missing_weeks"] = result["missing_weeks"].astype("int64")
