# MECH_B confirmation program I02 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: s = df.set_index(monthly_spend).age; s[10:30]
import pandas as pd
df = pd.read_csv("customers.csv")
s = df.set_index("monthly_spend").age
result = s[10:30]
