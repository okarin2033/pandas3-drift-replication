# Reference solution for A_CONV_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str})
metres = (trips['distance_km'] * 1000).round().astype('int64')
result = metres.groupby(trips['rider_id']).sum().sort_index()
result.name = 'metres'
