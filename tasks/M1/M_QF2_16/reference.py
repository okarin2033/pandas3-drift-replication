# M_QF2_16 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("appointments.csv")
cnt = {}
for s in df["local_start"].tolist():
    h = (dt.datetime.strptime(s, "%Y-%m-%d %H:%M") + dt.timedelta(days=14)).hour
    cnt[h] = cnt.get(h, 0) + 1
keys = sorted(cnt)
result = pd.Series([cnt[k] for k in keys], index=pd.Index(keys, dtype="int64"), dtype="int64")
