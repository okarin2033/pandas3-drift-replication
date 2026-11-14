# MECH_B confirmation program R01 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: pd.concat([a, b], axis=1, sort=False) with date indexes
import pandas as pd
a = pd.read_csv("left.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "left"})
b = pd.read_csv("right.csv", parse_dates=["date"], index_col="date").rename(columns={"value": "right"})
result = pd.concat([a, b], axis=1, sort=False)
