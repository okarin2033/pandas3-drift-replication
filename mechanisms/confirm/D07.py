# MECH_A confirm program D07 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): to_datetime on numeric strings with unit="s" (all columns read as text to keep ids).
import pandas as pd

df = pd.read_csv("events.csv", dtype=str)
df["ts"] = pd.to_datetime(df["epoch_s"], unit="s")
result = df[["event_id", "ts"]]
