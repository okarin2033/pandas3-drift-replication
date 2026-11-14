# M_QF2_11 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("sessions.csv")
t = pd.to_datetime(df["started_at"]).sort_values()
secs = t.astype("int64") / 1e9
result = float(secs.diff().median())
