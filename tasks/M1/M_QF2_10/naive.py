# M_QF2_10 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("sessions.csv")
df["started_at"] = pd.to_datetime(df["started_at"])
df = df.sort_values("started_at")
result = df["started_at"].dt.to_pydatetime()[0]
