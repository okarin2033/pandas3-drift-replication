# MECH_A confirm program L02 (LOUD_CONTEXT). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): fillna(method="ffill").
import pandas as pd

df = pd.read_csv("readings.csv")
result = df["value"].fillna(method="ffill")
