# MECH_B confirmation program I05 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: Index == Series returns Series (b)
# Why a second attempt: attempt a (Series * list) gave IDENTICAL
import pandas as pd
df = pd.read_csv("items.csv")
result = pd.Index(df["old_code"]) == df["new_code"]
