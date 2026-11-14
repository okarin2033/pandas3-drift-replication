# MECH_A confirm program L05 (LOUD_CONTEXT). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): DataFrame.applymap(str.strip).
import pandas as pd

df = pd.read_csv("names.csv")
result = df.applymap(str.strip)
