# MECH_B confirmation program I01 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: total = np.sum(df[[quantity, amount]])
import numpy as np
import pandas as pd
df = pd.read_csv("orders.csv")
result = np.sum(df[["quantity", "amount"]])
