# MECH_B confirmation program I05 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: s * [1, 2, 3] (attempt a)
import pandas as pd
df = pd.read_csv("items.csv")
result = df.qty * [1, 2, 3]
