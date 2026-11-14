# F-main re-check program for catalogue row S06 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/S06.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: shops.csv -> branch_sales.csv, shop_code -> branch_code
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("branch_sales.csv", dtype={"branch_code": "category"})
result = df.groupby("branch_code", observed=True)["sales"].sum()
