# MECH_B confirmation program X01 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.x.rolling(7).std() ; rolling(7).sem()
import pandas as pd
df = pd.read_csv("series.csv")
result = pd.DataFrame({"std": df.x.rolling(7).std(), "sem": df.x.rolling(7).sem()})
