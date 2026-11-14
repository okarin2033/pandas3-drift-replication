# F-main re-check program for catalogue row D03 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/D03.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: sales.csv -> shipments.csv, sale_date -> ordered_on, amount -> value
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("shipments.csv")
df["month_end"] = pd.to_datetime(df["ordered_on"]).dt.to_period("M").dt.end_time
result = df.groupby("month_end")["value"].sum()
