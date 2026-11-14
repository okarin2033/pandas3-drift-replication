# MECH_A confirm program C06 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): build an Index from a NumPy array, then change the array.
import pandas as pd

df = pd.read_csv("levels.csv")
arr = df["level"].to_numpy()
idx = pd.Index(arr)
arr[0] = 99
result = idx
