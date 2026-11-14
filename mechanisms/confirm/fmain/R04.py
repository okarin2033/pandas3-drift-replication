# F-main re-check program for catalogue row R04 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/R04.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: scores.csv -> exam_scores.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("exam_scores.csv", index_col="student")
result = df.stack()
