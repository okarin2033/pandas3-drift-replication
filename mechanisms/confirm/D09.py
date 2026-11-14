# MECH_A confirm program D09 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): infer_freq on quarter-start dates.
import pandas as pd

df = pd.read_csv("quarters.csv")
result = pd.infer_freq(pd.DatetimeIndex(pd.to_datetime(df["quarter_start"])))
