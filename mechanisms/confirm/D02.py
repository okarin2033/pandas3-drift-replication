# MECH_A confirm program D02 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): to_datetime(epoch seconds, unit="s") then astype("int64").
import pandas as pd

df = pd.read_csv("events.csv")
df["ts"] = pd.to_datetime(df["epoch_s"], unit="s")
result = df["ts"].astype("int64")
