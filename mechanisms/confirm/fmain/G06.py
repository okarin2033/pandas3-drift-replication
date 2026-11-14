# F-main re-check program for catalogue row G06 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/G06_b.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: orders.csv -> subscribers.csv, plan -> tier, amount -> monthly_fee
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd
df = pd.read_csv("subscribers.csv").set_index("tier")
out = {}
for k, g in df.groupby(level=["tier"]):
    out[k] = g.monthly_fee.sum()
result = out
