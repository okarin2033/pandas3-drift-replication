# M_QF2_05 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
from datetime import timedelta
import pandas as pd

df = pd.read_csv("appointments.csv")
start = pd.to_datetime(df["local_start"]).dt.tz_localize("America/New_York")
df["reminder"] = start.map(lambda t: (t.to_pydatetime() - timedelta(days=1)).isoformat())
result = df[["appt_id", "reminder"]]
