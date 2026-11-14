# MECH_B confirmation program N07 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: cat.map(lambda v: x if pd.isna(v) else v) (attempt a)
import pandas as pd
df = pd.read_csv("grades.csv")
cat = df.grade.astype("category")
result = cat.map(lambda v: "missing" if pd.isna(v) else v.upper())
