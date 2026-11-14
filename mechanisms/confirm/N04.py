# MECH_B confirmation program N04 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.col.value_counts().index.dtype ; sorted index operations (attempt a)
import pandas as pd
df = pd.read_csv("orders.csv")
vc = df["qty"].astype(object).value_counts()
result = vc.sort_index()
