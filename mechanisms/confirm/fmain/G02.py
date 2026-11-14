# F-main re-check program for catalogue row G02 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/G02.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: sales.csv -> unit_sales.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("unit_sales.csv")
df["region"] = df["region"].astype(pd.CategoricalDtype(["north", "south", "west"]))
result = df.groupby(["region", "channel"], observed=False)[["units"]].apply(lambda x: x.sum())
