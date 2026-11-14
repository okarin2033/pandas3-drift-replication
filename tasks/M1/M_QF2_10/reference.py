# M_QF2_10 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("sessions.csv")
result = min(dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S") for s in df["started_at"].tolist())
