# M_QF2_01 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("signups.csv")
first, last = {}, {}
epoch = dt.date(1970, 1, 1)
for ch, day in zip(df["channel"].tolist(), df["signup_day"].tolist()):
    if not isinstance(ch, str):
        continue
    k = ch.strip().lower()
    secs = (dt.date.fromisoformat(day) - epoch).days * 86400
    first[k] = min(first.get(k, secs), secs)
    last[k] = max(last.get(k, secs), secs)
keys = sorted(first)
result = pd.DataFrame({"first_signup": [first[k] for k in keys], "last_signup": [last[k] for k in keys]},
                      index=pd.Index(keys)).astype("int64")
