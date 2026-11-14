# F-main re-check program for catalogue row C05 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/C05.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: measures.csv -> gauges.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("gauges.csv")
b = df.astype({"reading": "float64"}, copy=False)
b.iloc[0, 1] = 0.0
result = df
