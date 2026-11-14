# M_QF2_04 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("signups.csv")
days = [dt.date.fromisoformat(s) for s in df["signup_day"].tolist()]
first, last = min(days), max(days)
cnt = {}
for d in days:
    cnt[d] = cnt.get(d, 0) + 1
epoch = dt.date(1970, 1, 1)
keys, vals = [], []
d = first
while d <= last:
    keys.append((d - epoch).days * 86400)
    vals.append(cnt.get(d, 0))
    d += dt.timedelta(days=1)
result = pd.Series(vals, index=pd.Index(keys, dtype="int64"), dtype="int64")
