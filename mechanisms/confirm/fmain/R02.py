# F-main re-check program for catalogue row R02 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/R02.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: customers.csv -> memberships.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("memberships.csv")
result = df[["plan", "city"]].value_counts(sort=False).head(3)
