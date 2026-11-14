# MECH_A confirm program S02 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): None written into a text column, later tested with "is None".
import pandas as pd

df = pd.read_csv("customers.csv")
df.loc[df["city"] == "-", "city"] = None
df["city_label"] = df["city"].map(lambda v: "unknown" if v is None else v)
result = df["city_label"].value_counts(dropna=False).sort_index()
