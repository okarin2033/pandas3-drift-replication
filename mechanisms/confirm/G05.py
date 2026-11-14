# MECH_B confirmation program G05 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.groupby(plan).monthly_spend.agg(np.std)
import numpy as np
import pandas as pd
df = pd.read_csv("customers.csv")
result = df.groupby("plan").monthly_spend.agg(np.std)
