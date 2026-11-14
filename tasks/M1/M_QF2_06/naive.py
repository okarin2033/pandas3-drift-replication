# M_QF2_06 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("appointments.csv")
start = pd.to_datetime(df["local_start"]).dt.tz_localize("America/New_York")
slot = start + pd.offsets.Day(1)
df["next_day_slot"] = slot.dt.strftime("%Y-%m-%d %H:%M")
result = df[["appt_id", "next_day_slot"]]
