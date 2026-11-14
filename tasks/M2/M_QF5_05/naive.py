# M_QF5_05: naive solution using the invited idiom of catalogue row R01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

north = pd.read_csv("footfall_north.csv", parse_dates=["day"], index_col="day")
south = pd.read_csv("footfall_south.csv", parse_dates=["day"], index_col="day")
both = pd.concat([north["visitors"], south["visitors"]], axis=1, sort=False)
result = both.fillna(0).sum(axis=1).diff()
