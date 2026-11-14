# MECH_B confirmation program I06 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df[[flag, count]].sum(axis=1) (b: counts near the int64 limit)
# Why a second attempt: attempt a (small counts) gave DTYPE_ONLY on E1 and IDENTICAL on E2
import pandas as pd
df = pd.read_csv("big.csv")
result = df[["flag", "count"]].sum(axis=1)
