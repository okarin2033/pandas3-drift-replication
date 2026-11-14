# F-main re-check program for catalogue row N05 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/N05_b.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: scores.csv -> quiz_scores.csv, math -> quiz_a, art -> quiz_b
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("quiz_scores.csv")
threshold = pd.Series({"quiz_a": 5, "quiz_b": 3}, dtype="Int64")
result = df > threshold
