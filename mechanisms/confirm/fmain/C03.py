# F-main re-check program for catalogue row C03 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/C03.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: transactions.csv -> bookings.csv, amount -> total
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("bookings.csv")
amounts = df["total"]
amounts[amounts < 0] = 0
result = df["total"].sum()
