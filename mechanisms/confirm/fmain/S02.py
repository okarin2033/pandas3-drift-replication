# F-main re-check program for catalogue row S02 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/S02.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: customers.csv -> members.csv, city -> home_city
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("members.csv")
df.loc[df["home_city"] == "-", "home_city"] = None
df["city_label"] = df["home_city"].map(lambda v: "unknown" if v is None else v)
result = df["city_label"].value_counts(dropna=False).sort_index()
