# F-main re-check program for catalogue row D04 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/D04.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: readings.csv -> signups.csv, reading_date -> signup_day
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("signups.csv")
days = pd.date_range(df["signup_day"].min(), df["signup_day"].max(), freq="D")
result = pd.Series(days.astype("int64"), name="day_int")
