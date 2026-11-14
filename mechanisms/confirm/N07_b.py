# MECH_B confirmation program N07 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: cat_series.replace(a, z) (b)
# Why a second attempt: attempt a (Categorical.map with a NaN-aware function) gave DTYPE_ONLY
import pandas as pd
df = pd.read_csv("grades.csv")
cat = df.grade.astype("category")
result = cat.replace("a", "z").value_counts()
