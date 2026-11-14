# Reference solution for A_MRG_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
sky = {o: s.strip().lower() for o, s in zip(w['observed_at'].tolist(), w['sky'].tolist())}
n, ds, dn = {}, {}, {}
for s, d in zip(trips['started_at'].tolist(), trips['duration_min'].tolist()):
    if s[:7] != '2025-09':
        continue
    k = sky[s[:13] + ':00']
    n[k] = n.get(k, 0) + 1
    if d != '':
        ds[k] = ds.get(k, 0) + int(round(float(d)))
        dn[k] = dn.get(k, 0) + 1
keys = sorted(n)
result = pd.DataFrame({'trips': [n[k] for k in keys], 'mean_duration_min': [round(ds[k] / dn[k], 1) for k in keys]},
                      index=pd.Index(keys, name='sky'))
