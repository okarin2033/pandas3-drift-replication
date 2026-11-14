# F-main re-check program for catalogue row I01 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/I01.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: orders.csv -> order_lines.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import numpy as np
import pandas as pd
df = pd.read_csv("order_lines.csv")
result = np.sum(df[["quantity", "amount"]])
