# F-main re-check program for catalogue row N01 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/N01_b.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: orders.csv -> deliveries.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("deliveries.csv")
df["shipped"] = df.status.replace({"shipped": 1, "pending": 0})
result = df.groupby("city").mean(numeric_only=True)
