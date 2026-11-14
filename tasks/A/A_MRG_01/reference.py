# Reference solution for A_MRG_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str, 'start_station': str, 'end_station': str})
stations = pd.read_csv('stations.csv', dtype={'station_code': str})
district_of = {str(c): str(d).strip().title() for c, d in zip(stations['station_code'], stations['district'])}
districts = pd.Series([district_of.get(str(s)) for s in trips['start_station']], name='district')
counts = districts.groupby(districts).size().sort_index()
result = pd.Series([int(v) for v in counts.to_numpy()], index=pd.Index([str(k) for k in counts.index], name='district'),
                   name='count')
