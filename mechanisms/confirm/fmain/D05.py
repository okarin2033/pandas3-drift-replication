# F-main re-check program for catalogue row D05 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/D05_b.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: reminders.csv -> appointments.csv, local_time -> local_start, meeting_id -> appt_id
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
from datetime import timedelta
import pandas as pd

df = pd.read_csv("appointments.csv")
df["ts"] = pd.to_datetime(df["local_start"]).dt.tz_localize("US/Eastern")
df["reminder"] = df["ts"].map(lambda t: (t.to_pydatetime() + timedelta(days=1)).isoformat())
result = df[["appt_id", "reminder"]]
