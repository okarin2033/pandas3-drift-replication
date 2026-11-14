# MECH_A confirm program L04 (LOUD_CONTEXT). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): setitem of a float into a text column.
import pandas as pd

df = pd.read_csv("items.csv")
ser = df["label"].copy()
ser[1] = 2.5
result = ser
