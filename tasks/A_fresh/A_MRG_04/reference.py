# Reference solution for A_MRG_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
stations = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
district = {c: ' '.join(w[:1].upper() + w[1:].lower() for w in d.split())
            for c, d in zip(stations['station_code'].tolist(), stations['district'].tolist())}
n, km = {}, {}
for s, d in zip(trips['start_station'].tolist(), trips['distance_km'].tolist()):
    k = district[s]
    n[k] = n.get(k, 0) + 1
    km[k] = km.get(k, 0) + int(round(float(d) * 100))
keys = sorted(n)
result = pd.DataFrame({'trips': [n[k] for k in keys], 'total_km': [round(km[k] / 100, 2) for k in keys]},
                      index=pd.Index(keys, name='district'))
