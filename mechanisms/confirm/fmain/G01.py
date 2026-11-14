# F-main re-check program for catalogue row G01 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/G01.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: customers.csv -> subscribers.csv, monthly_spend -> monthly_fee
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("subscribers.csv")
bins = [0, 18, 30, 45, 60, 100]
labels = ["under_18", "18_29", "30_44", "45_59", "60_plus"]
result = df.groupby(pd.cut(df.age, bins, labels=labels)).monthly_fee.agg(["count", "mean"])
