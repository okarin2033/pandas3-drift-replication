# MECH_B confirmation program N03 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df[k] = idx_obj (b: Index built from an object Series, set as a column, then summarised)
# Why a second attempt: attempt a (Series constructor on an object Series) gave DTYPE_ONLY (no inference on 2.3.3 either)
import pandas as pd
df = pd.read_csv("items.csv")
codes = pd.Index(df["qty"].astype(object))
df["qty_code"] = codes
result = df.describe()
