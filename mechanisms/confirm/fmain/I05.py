# F-main re-check program for catalogue row I05 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/I05_b.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: items.csv -> code_changes.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("code_changes.csv")
result = pd.Index(df["old_code"]) == df["new_code"]
