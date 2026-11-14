# MECH_B confirmation program I06 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df[[flag, count]].sum(axis=1) (attempt a)
import pandas as pd
df = pd.read_csv("rows.csv")
result = df[["flag", "count"]].sum(axis=1)
