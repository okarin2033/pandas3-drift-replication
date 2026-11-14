# MECH_B confirmation program N03 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: pd.Series(obj_series_of_ints) (attempt a: constructor on an object Series, then a summary)
import pandas as pd
df = pd.read_csv("items.csv")
obj = df["qty"].astype(object)
s = pd.Series(obj)
result = s.describe()
