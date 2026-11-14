# MECH_A confirm program C04 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): the return value of an inplace method is stored.
import pandas as pd

df = pd.read_csv("inventory.csv")
result = df.fillna(0, inplace=True)
