# MECH_B confirmation program R07 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: a.join(b, how=left) with int and str-like index (attempt a)
import pandas as pd
a = pd.read_csv("left.csv").set_index("key")
b = pd.read_csv("right.csv").set_index("key")
result = a.join(b, how="left")
