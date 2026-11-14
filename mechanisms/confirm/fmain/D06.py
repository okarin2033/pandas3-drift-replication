# F-main re-check program for catalogue row D06 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/D06.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: shifts.csv -> appointments.csv, start_local -> local_start, shift_id -> appt_id
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("appointments.csv")
df["start"] = pd.to_datetime(df["local_start"]).dt.tz_localize("US/Eastern")
df["next_day_start"] = df["start"] + pd.offsets.Day(1)
result = df[["appt_id", "next_day_start"]]
