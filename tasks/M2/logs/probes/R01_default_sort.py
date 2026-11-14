# Probe (pkg:TASKS_M2, 2026-11-11): the R01 tasks' concat WITHOUT a sort argument, to document why the naive solutions pass
# sort=False explicitly. Not a task program.
import pandas as pd

north = pd.read_csv("footfall_north.csv", parse_dates=["day"], index_col="day")
south = pd.read_csv("footfall_south.csv", parse_dates=["day"], index_col="day")
result = pd.concat([north["visitors"].rename("north"), south["visitors"].rename("south")], axis=1)
