# M_QF2_11 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import statistics
import pandas as pd

df = pd.read_csv("sessions.csv")
ts = sorted(dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S") for s in df["started_at"].tolist())
gaps = [(b - a).total_seconds() for a, b in zip(ts[:-1], ts[1:])]
result = float(statistics.median(gaps))
