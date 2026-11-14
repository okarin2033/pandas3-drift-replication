# MECH_A confirm program S03 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): astype(str) on a text column with missing values, title case, value counts.
import pandas as pd

df = pd.read_csv("customers.csv")
result = df["city"].astype(str).str.title().value_counts().sort_index()
