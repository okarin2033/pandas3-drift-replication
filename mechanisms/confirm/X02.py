# MECH_B confirmation program X02 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.groupby(k).x.quantile(.5, interpolation=nearest) (attempt a)
import pandas as pd
df = pd.read_csv("scores.csv")
result = df.groupby("k").x.quantile(0.5, interpolation="nearest")
