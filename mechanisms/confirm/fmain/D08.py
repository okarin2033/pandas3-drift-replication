# F-main re-check program for catalogue row D08 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/D08.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: orders.csv -> shipments.csv, order_date -> ordered_on, ship_date -> shipped_on
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("shipments.csv", parse_dates=["ordered_on", "shipped_on"])
date_cols = df.select_dtypes(include="datetime64[ns]").columns
for c in date_cols:
    df[c] = df[c].dt.strftime("%Y-%m")
result = df
