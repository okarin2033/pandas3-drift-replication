# F-main re-check program for catalogue row O01 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/O01.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: prices.csv -> price_list.csv
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import json
from decimal import Decimal
import pandas as pd

df = pd.read_csv("price_list.csv", converters={"price": Decimal})
result = json.loads(df.to_json(orient="records"))
