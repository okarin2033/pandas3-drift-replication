# MECH_B confirmation program G06 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: for k, g in df.groupby([plan]): out[k] = g.amount.sum()
import pandas as pd
df = pd.read_csv("orders.csv")
out = {}
for k, g in df.groupby(["plan"]):
    out[k] = g.amount.sum()
result = out
