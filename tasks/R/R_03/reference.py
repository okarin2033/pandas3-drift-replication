# Reference solution for R_03 (stratum R, question 80001493). drafted_by: pkg:R_BUILD; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4 (csv module, results built from Python lists).
import csv
import pandas as pd

with open('stations.csv', encoding='utf-8', newline='') as f:
    lookup = {r['station_code']: int(r['docks']) for r in csv.DictReader(f)}
with open('trips.csv', encoding='utf-8', newline='') as f:
    trips = list(csv.DictReader(f))
result = pd.DataFrame({'start_station': [lookup.get(t['start_station'], t['start_station']) for t in trips],
                       'end_station': [lookup.get(t['end_station'], t['end_station']) for t in trips]})
