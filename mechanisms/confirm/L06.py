# MECH_A confirm program L06 (LOUD_CONTEXT). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): groupby.apply with a function that reads the grouping column.
import pandas as pd

df = pd.read_csv("readings.csv")
result = df.groupby("sensor_id").apply(lambda g: g["sensor_id"].iloc[0] + ":" + str(g["value"].sum()))
