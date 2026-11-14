# MECH_B confirmation program R02 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df[[plan, city]].value_counts(sort=False).head(3)
import pandas as pd
df = pd.read_csv("customers.csv")
result = df[["plan", "city"]].value_counts(sort=False).head(3)
