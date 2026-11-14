# MECH_B confirmation program N06 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.convert_dtypes().x.rank()
import pandas as pd
df = pd.read_csv("values.csv")
result = df.convert_dtypes().x.rank()
