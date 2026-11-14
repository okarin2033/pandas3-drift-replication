# F-main re-check program for catalogue row G03 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/G03.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: orders.csv -> purchases.csv, customer_id -> subscriber_id
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("purchases.csv")
result = df.groupby("subscriber_id").apply(lambda g: g.sum(numeric_only=True))
