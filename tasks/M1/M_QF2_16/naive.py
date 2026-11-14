# M_QF2_16 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("appointments.csv")
start = pd.to_datetime(df["local_start"]).dt.tz_localize("America/New_York")
checkup = start + pd.offsets.Day(14)
result = checkup.dt.hour.value_counts().sort_index()
