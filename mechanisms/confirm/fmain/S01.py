# F-main re-check program for catalogue row S01 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/S01.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: customers.csv -> members.csv, city -> home_city, amount -> fee
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("members.csv")
text_cols = [c for c in df.columns if df[c].dtype == object]
for c in text_cols:
    df[c] = df[c].str.strip().str.title()
result = df.groupby("home_city")["fee"].sum()
