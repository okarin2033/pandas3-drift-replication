# MECH_A confirm program S01 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): select text columns with dtype == object and clean only those; total amount per city.
import pandas as pd

df = pd.read_csv("customers.csv")
text_cols = [c for c in df.columns if df[c].dtype == object]
for c in text_cols:
    df[c] = df[c].str.strip().str.title()
result = df.groupby("city")["amount"].sum()
