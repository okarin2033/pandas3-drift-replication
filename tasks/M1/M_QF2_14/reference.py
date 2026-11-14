# M_QF2_14 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("shipments.csv")
have = {dt.date.fromisoformat(s) for s in df["ordered_on"].tolist()}
epoch = dt.date(1970, 1, 1)
out = []
d = min(have)
while d <= max(have):
    if d not in have:
        out.append((d - epoch).days)
    d += dt.timedelta(days=1)
result = out
