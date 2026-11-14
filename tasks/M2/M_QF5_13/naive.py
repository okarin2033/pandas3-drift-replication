# M_QF5_13: naive solution using the invited idiom of catalogue row R01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

north = pd.read_csv("footfall_north.csv", parse_dates=["day"], index_col="day")
south = pd.read_csv("footfall_south.csv", parse_dates=["day"], index_col="day")
table = pd.concat([north["visitors"].rename("north"), south["visitors"].rename("south")], axis=1, sort=False)
result = table.head(10)
