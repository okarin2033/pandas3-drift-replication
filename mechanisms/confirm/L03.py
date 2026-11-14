# MECH_A confirm program L03 (LOUD_CONTEXT). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): to_numeric(errors="ignore").
import pandas as pd

df = pd.read_csv("raw.csv")
result = pd.to_numeric(df["value"], errors="ignore")
