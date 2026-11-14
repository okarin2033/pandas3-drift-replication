# MECH_B confirmation program R05 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: pd.concat([df_part, df_empty_or_allNA]) (then the usual summary)
import pandas as pd
jan = pd.read_csv("jan.csv")
feb = pd.read_csv("feb.csv")
combined = pd.concat([jan, feb], ignore_index=True)
result = combined.describe()
