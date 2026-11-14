# M_QF5_13: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd


def read_rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return [(r["day"], int(r["visitors"])) for r in csv.DictReader(f)]


north = read_rows("footfall_north.csv")
south = read_rows("footfall_south.csv")
n_map, s_map = dict(north), dict(south)
days = [d for d, _ in north] + [d for d, _ in south if d not in n_map]
days = days[:10]
result = pd.DataFrame(
    {"north": np.array([float(n_map[d]) if d in n_map else np.nan for d in days], dtype="float64"),
     "south": np.array([float(s_map[d]) if d in s_map else np.nan for d in days], dtype="float64")},
    index=pd.DatetimeIndex(pd.to_datetime(days, format="%Y-%m-%d"), name="day"))
