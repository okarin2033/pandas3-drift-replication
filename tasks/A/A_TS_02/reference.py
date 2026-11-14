# Reference solution for A_TS_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

trips = pd.read_csv('trips.csv')
day = pd.to_datetime(trips['started_at'], format='%Y-%m-%d %H:%M').dt.normalize()
per_day = day.groupby(day).size()
days = pd.date_range(per_day.index.min(), per_day.index.max(), freq='D', name='day')
counts = np.array([int(per_day.get(d, 0)) for d in days], dtype='int64')
cum = np.concatenate([[0], np.cumsum(counts)])
values = [np.nan] * 6 + [(int(cum[i + 1]) - int(cum[i - 6])) / 7 for i in range(6, len(counts))]
result = pd.Series(values, index=days, name='rolling_mean_7d')
