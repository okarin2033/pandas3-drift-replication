# MECH_A confirm program D06 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): tz-aware timestamp + offsets.Day(1) across a DST change.
import pandas as pd

df = pd.read_csv("shifts.csv")
df["start"] = pd.to_datetime(df["start_local"]).dt.tz_localize("US/Eastern")
df["next_day_start"] = df["start"] + pd.offsets.Day(1)
result = df[["shift_id", "next_day_start"]]
