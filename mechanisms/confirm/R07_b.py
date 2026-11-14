# MECH_B confirmation program R07 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: a.join(b, how=left) with int and str-like index (b: the joined key then summarised)
# Why a second attempt: attempt a gave DTYPE_ONLY (index dtype object on 2.3.3, int64 on 3.1.1)
import pandas as pd
a = pd.read_csv("left.csv").set_index("key")
b = pd.read_csv("right.csv").set_index("key")
joined = a.join(b, how="left")
result = joined.reset_index().describe()
