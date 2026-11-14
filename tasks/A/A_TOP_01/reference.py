# Reference solution for A_TOP_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str})
cents = (trips['distance_km'] * 100).round().astype('int64')
per_rider = cents.groupby(trips['rider_id']).sum()
table = pd.DataFrame({'rider_id': [str(k) for k in per_rider.index], 'cents': [int(v) for v in per_rider.to_numpy()]})
table = table.sort_values(['cents', 'rider_id'], ascending=[False, True], kind='mergesort').head(5)
result = pd.DataFrame({'rider_id': table['rider_id'].tolist(), 'total_km': [round(c / 100, 2) for c in table['cents']]})
