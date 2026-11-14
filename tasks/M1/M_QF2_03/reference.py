# M_QF2_03 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import math
import pandas as pd

df = pd.read_csv("shipments.csv")
tot = {}
for d, v in zip(df["ordered_on"].tolist(), df["value"].tolist()):
    y, m = int(d[:4]), int(d[5:7])
    tot.setdefault((y, m), []).append(float(v))
keys = sorted(tot)
ends = []
for y, m in keys:
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    ends.append(pd.Timestamp(year=ny, month=nm, day=1).as_unit("ns") - pd.Timedelta(1, "ns"))
idx = pd.DatetimeIndex(ends).as_unit("ns")
result = pd.Series([round(math.fsum(tot[k]), 2) for k in keys], index=idx)
