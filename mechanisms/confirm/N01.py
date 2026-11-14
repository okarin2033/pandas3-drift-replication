# MECH_B confirmation program N01 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: s = df.status.replace({shipped: 1, pending: 0}); s.sum() / s.sort_values() (attempt a: sorted codes)
import pandas as pd
df = pd.read_csv("orders.csv")
s = df.status.replace({"shipped": 1, "pending": 0})
result = s.sort_values()
