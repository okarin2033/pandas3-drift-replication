# MECH_B confirmation program G08 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: groupby.sum on very large ints (attempt a)
import pandas as pd
df = pd.read_csv("accounts.csv")
result = df.groupby("k").balance.sum()
