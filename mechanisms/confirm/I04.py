# MECH_B confirmation program I04 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: mask1 & [True, False, True] (attempt a)
import pandas as pd
df = pd.read_csv("flags.csv")
mask1 = df.active
result = df[mask1 & [True, False, True]]
