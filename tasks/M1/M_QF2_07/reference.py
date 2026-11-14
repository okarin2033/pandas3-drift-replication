# M_QF2_07 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("clicks.csv", dtype=str)
cnt = {}
for s in df["epoch_s"].tolist():
    try:
        day = dt.datetime.fromtimestamp(int(s), tz=dt.timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        continue
    cnt[day] = cnt.get(day, 0) + 1
keys = sorted(cnt)
result = pd.Series([cnt[k] for k in keys], index=pd.Index(keys), dtype="int64")
