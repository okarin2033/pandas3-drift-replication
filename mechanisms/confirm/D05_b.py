# MECH_A confirm program D05 (attempt 2, written after attempt 1 gave no value drift). drafted_by: pkg:MECH_A, 2026-11-11.
# Idea (catalogue, description "pytz-specific code differs"): the localised time zone object is used with standard-library
# datetime arithmetic (reminder one day later, via to_pydatetime + timedelta) across a DST change.
from datetime import timedelta
import pandas as pd

df = pd.read_csv("reminders.csv")
df["ts"] = pd.to_datetime(df["local_time"]).dt.tz_localize("US/Eastern")
df["reminder"] = df["ts"].map(lambda t: (t.to_pydatetime() + timedelta(days=1)).isoformat())
result = df[["meeting_id", "reminder"]]
