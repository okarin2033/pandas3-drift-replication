# MECH_B confirmation program G06 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: for k, g in df.groupby([plan]) ... (b: grouping by level given as a list of length 1)
# Why a second attempt: attempt a (column list of length 1) gave IDENTICAL on E1/E2; the 3.0 removal note names the level-list case
import pandas as pd
df = pd.read_csv("orders.csv").set_index("plan")
out = {}
for k, g in df.groupby(level=["plan"]):
    out[k] = g.amount.sum()
result = out
