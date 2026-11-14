# F-main re-check program for catalogue row N02 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/N02.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: stores.csv -> store_traffic.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("store_traffic.csv").convert_dtypes()
ratio = df.sales / df.visits
result = ratio.isna().sum()
