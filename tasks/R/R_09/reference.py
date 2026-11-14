# Reference solution for R_09 (stratum R, question 79968177). drafted_by: pkg:R_BUILD; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4 (csv module, results built from Python lists).
import csv
import pandas as pd

with open('trips.csv', encoding='utf-8', newline='') as f:
    trips = list(csv.DictReader(f))
cents = [int(round(float(t['distance_km']) * 100)) for t in trips]
per = {}
for t, c in zip(trips, cents):
    per[t['rider_id']] = per.get(t['rider_id'], 0) + c
ids = sorted(per)
result = {'total': sum(cents) / 100, 'row_count': len(trips),
          'per_rider': pd.Series([per[i] / 100 for i in ids], index=pd.Index(ids, name='rider_id'), name='distance_km',
                                 dtype='float64')}
