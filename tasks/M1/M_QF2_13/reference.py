# M_QF2_13 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("quarterly_revenue.csv")
ends = []
for d in df["quarter_start"].tolist():
    y, m = int(d[:4]), int(d[5:7])
    m2 = m + 3
    ny, nm = (y + 1, m2 - 12) if m2 > 12 else (y, m2)
    ends.append(pd.Timestamp(year=ny, month=nm, day=1).as_unit("ns") - pd.Timedelta(1, "ns"))
out = pd.DataFrame({"quarter_end": pd.DatetimeIndex(ends).as_unit("ns"), "revenue": df["revenue"].astype("int64").tolist()})
result = out.sort_values("quarter_end", kind="mergesort").reset_index(drop=True)
