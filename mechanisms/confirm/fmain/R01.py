# F-main re-check program for catalogue row R01 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/R01.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: left.csv -> footfall_north.csv, right.csv -> footfall_south.csv, date -> day, value -> visitors
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
a = pd.read_csv("footfall_north.csv", parse_dates=["day"], index_col="day").rename(columns={"visitors": "left"})
b = pd.read_csv("footfall_south.csv", parse_dates=["day"], index_col="day").rename(columns={"visitors": "right"})
result = pd.concat([a, b], axis=1, sort=False)
