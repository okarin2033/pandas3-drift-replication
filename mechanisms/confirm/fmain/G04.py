# F-main re-check program for catalogue row G04 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/G04.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: orders.csv -> purchases.csv, city -> store_city, amount -> spend
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("purchases.csv")
result = df.groupby(df.store_city.str.title(), as_index=False).spend.sum()
