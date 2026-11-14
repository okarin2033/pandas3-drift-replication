# Reference solution for A_DATE_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
joined = pd.to_datetime(riders['joined_on'], format='%Y-%m-%d').dropna()
parts = pd.DataFrame({'year': joined.dt.year.astype('int64').to_numpy(),
                      'quarter': joined.dt.quarter.astype('int64').to_numpy()})
counts = parts.groupby(['year', 'quarter']).size()
result = pd.DataFrame({'year': [int(k[0]) for k in counts.index], 'quarter': [int(k[1]) for k in counts.index],
                       'n_riders': [int(v) for v in counts.to_numpy()]})
result = result.sort_values(['year', 'quarter'], kind='mergesort').reset_index(drop=True)
