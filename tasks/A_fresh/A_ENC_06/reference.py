# Reference solution for A_ENC_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
s, n = {}, {}
for st, r in zip(trips['start_station'].tolist(), trips['rating'].tolist()):
    if r != '':
        s[st] = s.get(st, 0) + int(round(float(r)))
        n[st] = n.get(st, 0) + 1
enc = {k: round(s[k] / n[k], 2) for k in n}
result = pd.Series([enc.get(st) for st in trips['start_station'].tolist()],
                   index=pd.Index([int(t) for t in trips['trip_id'].tolist()], name='trip_id'), name='station_rating', dtype='float64')
