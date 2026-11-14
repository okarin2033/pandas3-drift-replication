# F-main re-check program for catalogue row I02 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/I02.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: customers.csv -> parcel_rates.csv, monthly_spend -> weight_kg, age -> fee
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("parcel_rates.csv")
s = df.set_index("weight_kg").fee
result = s[10:30]
