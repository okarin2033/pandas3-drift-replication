# MECH_A confirm program D07 (attempt 2, written after attempt 1 was LOUD on 3.x, not drift). drafted_by: pkg:MECH_A, 2026-11-11.
# Idea (catalogue): to_datetime on numeric strings with unit="s", with the common defensive errors="coerce".
import pandas as pd

df = pd.read_csv("events.csv", dtype=str)
df["ts"] = pd.to_datetime(df["epoch_s"], unit="s", errors="coerce")
result = df[["event_id", "ts"]]
