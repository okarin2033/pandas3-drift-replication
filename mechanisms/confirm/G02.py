# MECH_B confirmation program G02 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.groupby([key1, key2], observed=False)[[values]].apply(lambda x: x.sum()) with categorical key1
import pandas as pd
df = pd.read_csv("sales.csv")
df["region"] = df["region"].astype(pd.CategoricalDtype(["north", "south", "west"]))
result = df.groupby(["region", "channel"], observed=False)[["units"]].apply(lambda x: x.sum())
