# Reference solution for A_MRG_03 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'start_station': str})
changes = pd.read_csv('fare_changes.csv', dtype={'station_code': str})
fare_of = {str(c): float(f) for c, f in zip(changes['station_code'], changes['new_base_fare']) if f == f}
count = {}
for s in trips['start_station']:
    f = fare_of.get(str(s))
    if f is not None:
        count[f] = count.get(f, 0) + 1
keys = sorted(count)
result = pd.Series([count[k] for k in keys], index=pd.Index(keys, name='new_base_fare'), name='n_trips', dtype='int64')
