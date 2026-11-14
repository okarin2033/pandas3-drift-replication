# F-main re-check program for catalogue row X02 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/X02.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: scores.csv -> panel_scores.csv, k -> panel, x -> score
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("panel_scores.csv")
result = df.groupby("panel").score.quantile(0.5, interpolation="nearest")
