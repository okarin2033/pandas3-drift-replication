# MECH_B confirmation program G07 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.groupby(k).x.sum() with exact comparison (attempt a: mixed-magnitude amounts)
import pandas as pd
df = pd.read_csv("readings.csv")
result = df.groupby("k").x.sum()
