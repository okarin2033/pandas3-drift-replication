# MECH_A confirm program C06 (attempt 2, written after attempt 1 was LOUD on 3.x: the to_numpy() array was read-only).
# drafted_by: pkg:MECH_A, 2026-11-11. Idea (catalogue): build an Index from an own NumPy array, then change the array in place.
import numpy as np
import pandas as pd

df = pd.read_csv("levels.csv")
arr = np.array(df["level"], dtype="int64")
idx = pd.Index(arr)
arr -= arr.min()
result = idx
