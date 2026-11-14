# MECH_B confirmation program N02 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.convert_dtypes() then a ratio with zero denominators and isna().sum()
import pandas as pd
df = pd.read_csv("stores.csv").convert_dtypes()
ratio = df.sales / df.visits
result = ratio.isna().sum()
