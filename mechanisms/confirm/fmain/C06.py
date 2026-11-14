# F-main re-check program for catalogue row C06 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/C06_b.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: levels.csv -> gauges.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import numpy as np
import pandas as pd

df = pd.read_csv("gauges.csv")
arr = np.array(df["level"], dtype="int64")
idx = pd.Index(arr)
arr -= arr.min()
result = idx
