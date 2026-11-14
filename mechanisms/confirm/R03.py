# MECH_B confirmation program R03 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.nlargest(2, amount) with tied amounts (attempt a)
import pandas as pd
df = pd.read_csv("orders.csv")
result = df.nlargest(2, "amount")
