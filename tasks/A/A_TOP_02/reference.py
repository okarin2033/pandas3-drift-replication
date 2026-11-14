# Reference solution for A_TOP_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv')
known = trips[trips['duration_min'].notna()]
table = pd.DataFrame({'payment': [str(p).strip().lower() for p in known['payment']],
                      'trip_id': known['trip_id'].astype('int64').to_numpy(),
                      'duration_min': known['duration_min'].astype('int64').to_numpy()})
table = table.sort_values(['payment', 'duration_min', 'trip_id'], ascending=[True, False, True], kind='mergesort')
parts = [g.head(3) for _, g in table.groupby('payment', sort=True)]
result = pd.concat(parts, ignore_index=True)[['payment', 'trip_id', 'duration_min']]
