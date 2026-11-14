# F-main re-check program for catalogue row C01 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/C01.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: orders.csv -> bookings.csv, status -> state, amount -> total
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("bookings.csv")
df["total"][df["state"] == "cancelled"] = 0
result = df
