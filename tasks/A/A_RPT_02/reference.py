# Reference solution for A_RPT_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'start_station': str, 'end_station': str})
stations = pd.read_csv('stations.csv', dtype={'station_code': str})
codes = [str(c) for c in stations['station_code']]
starts, ends = dict.fromkeys(codes, 0), dict.fromkeys(codes, 0)
for s in trips['start_station']:
    if str(s) in starts:
        starts[str(s)] += 1
for e in trips['end_station']:
    if str(e) in ends:
        ends[str(e)] += 1
rows = [(c, starts[c], ends[c], ends[c] - starts[c]) for c in codes]
rows.sort(key=lambda r: -r[3])
result = pd.DataFrame({'starts': [r[1] for r in rows], 'ends': [r[2] for r in rows], 'net_flow': [r[3] for r in rows]},
                      index=pd.Index([r[0] for r in rows], name='station_code'))
