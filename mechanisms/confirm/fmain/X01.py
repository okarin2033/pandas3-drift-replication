# F-main re-check program for catalogue row X01 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/X01.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: series.csv -> daily_temps.csv, x -> temp_c
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("daily_temps.csv")
result = pd.DataFrame({"std": df.temp_c.rolling(7).std(), "sem": df.temp_c.rolling(7).sem()})
