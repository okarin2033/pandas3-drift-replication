# M_QF2_15 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
from datetime import timedelta, timezone
import pandas as pd

df = pd.read_csv("appointments.csv")
start = pd.to_datetime(df["local_start"]).dt.tz_localize("America/New_York")
df["follow_up_utc"] = start.map(
    lambda t: (t.to_pydatetime() + timedelta(weeks=4)).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M"))
result = df[["appt_id", "follow_up_utc"]]
