# MECH_A confirm program C02 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): df[col].fillna(median, inplace=True), then use df.
import pandas as pd

df = pd.read_csv("patients.csv")
df["age"].fillna(df["age"].median(), inplace=True)
result = df
