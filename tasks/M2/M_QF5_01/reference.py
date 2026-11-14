# M_QF5_01: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd


def read_counts(path):
    with open(path, encoding="utf-8", newline="") as f:
        return {r["day"]: int(r["visitors"]) for r in csv.DictReader(f)}


north = read_counts("footfall_north.csv")
south = read_counts("footfall_south.csv")
days = sorted(set(north) | set(south))
result = pd.DataFrame(
    {"north": np.array([float(north[d]) if d in north else np.nan for d in days], dtype="float64"),
     "south": np.array([float(south[d]) if d in south else np.nan for d in days], dtype="float64")},
    index=pd.DatetimeIndex(pd.to_datetime(days, format="%Y-%m-%d"), name="day"))
