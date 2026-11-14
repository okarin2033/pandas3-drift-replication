# MECH_B confirmation program G04 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.groupby(df.city.str.title(), as_index=False).amount.sum()
import pandas as pd
df = pd.read_csv("orders.csv")
result = df.groupby(df.city.str.title(), as_index=False).amount.sum()
