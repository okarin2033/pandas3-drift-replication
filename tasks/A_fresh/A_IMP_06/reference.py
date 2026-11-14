# Reference solution for A_IMP_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
dur = [int(round(float(d))) for d in trips['duration_min'].tolist() if d != '']
fill_d = int(round(sum(dur) / len(dur)))
cnt = {}
for r in trips['rating'].tolist():
    if r != '':
        v = int(round(float(r)))
        cnt[v] = cnt.get(v, 0) + 1
top = max(cnt.values())
fill_r = min(k for k, v in cnt.items() if v == top)
result = pd.DataFrame({'trip_id': [int(t) for t in trips['trip_id'].tolist()],
                       'duration_min': [int(round(float(d))) if d != '' else fill_d for d in trips['duration_min'].tolist()],
                       'rating': [int(round(float(r))) if r != '' else fill_r for r in trips['rating'].tolist()]})
