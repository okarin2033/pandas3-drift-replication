# MECH_B confirmation program G07 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.groupby(k).x.sum() with exact comparison (b: large values that cancel within a group)
# Why a second attempt: attempt a (mixed-magnitude amounts) differed only within the oracle tolerance (DTYPE_ONLY from the key index dtype)
import pandas as pd
df = pd.read_csv("ledger.csv")
result = df.groupby("k").x.sum()
