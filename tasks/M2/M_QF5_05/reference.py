# M_QF5_05: version-robust reference solution.
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
totals = [north.get(d, 0) + south.get(d, 0) for d in days]
changes = [np.nan] + [float(totals[i] - totals[i - 1]) for i in range(1, len(totals))]
result = pd.Series(np.array(changes, dtype="float64"),
                   index=pd.DatetimeIndex(pd.to_datetime(days, format="%Y-%m-%d"), name="day"))
