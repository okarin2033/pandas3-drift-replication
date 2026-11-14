# MECH_B confirmation program I03 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: s = df.set_index(name).age; s[0] (attempt a)
import pandas as pd
df = pd.read_csv("people.csv")
s = df.set_index("name").age
result = s[0]
