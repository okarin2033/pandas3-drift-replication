# Reference solution for A_TOP_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
rows = sorted((p.strip().lower(), -int(round(float(d) * 100)), int(t), float(d))
              for t, p, d in zip(trips['trip_id'].tolist(), trips['payment'].tolist(), trips['distance_km'].tolist()))
seen, keep = {}, []
for r in rows:
    if seen.get(r[0], 0) < 3:
        keep.append(r)
        seen[r[0]] = seen.get(r[0], 0) + 1
result = pd.DataFrame({'payment': [r[0] for r in keep], 'trip_id': [r[2] for r in keep], 'distance_km': [r[3] for r in keep]})
