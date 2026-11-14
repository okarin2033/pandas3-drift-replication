# M_QF2_09 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("quarterly_revenue.csv")
days = [dt.date.fromisoformat(s) for s in df["quarter_start"].tolist()]
ok = all(d.day == 1 and d.month in (1, 4, 7, 10) for d in days)
steps = [(b.year * 12 + b.month) - (a.year * 12 + a.month) for a, b in zip(days[:-1], days[1:])]
result = "QS-JAN" if ok and steps and all(s == 3 for s in steps) else None
