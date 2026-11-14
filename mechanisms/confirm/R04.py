# MECH_B confirmation program R04 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.stack() on frame with NaN cells
import pandas as pd
df = pd.read_csv("scores.csv", index_col="student")
result = df.stack()
