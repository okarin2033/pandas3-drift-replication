# F-main re-check program for catalogue row R05 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/R05.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: jan.csv -> returns_march.csv, feb.csv -> returns_april.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
jan = pd.read_csv("returns_march.csv")
feb = pd.read_csv("returns_april.csv")
combined = pd.concat([jan, feb], ignore_index=True)
result = combined.describe()
