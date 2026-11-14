# MECH_A confirm program C03 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): write through a column held in a variable, then use the parent frame.
import pandas as pd

df = pd.read_csv("transactions.csv")
amounts = df["amount"]
amounts[amounts < 0] = 0
result = df["amount"].sum()
