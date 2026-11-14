# Reference solution for A_RPT_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
dist = sum(int(round(float(d) * 100)) for d in trips['distance_km'].tolist())
dur = [int(round(float(d))) for d in trips['duration_min'].tolist() if d != '']
rat = [int(round(float(r))) for r in trips['rating'].tolist() if r != '']
values = [len(trips), len(set(trips['rider_id'].tolist())), round(dist / 100, 2), round(sum(dur) / len(dur), 1),
          round(sum(rat) / len(rat), 2), sum(1 for f in trips['fare'].tolist() if f == '')]
result = pd.Series([float(v) for v in values],
                   index=['trips', 'riders', 'total_km', 'mean_duration_min', 'mean_rating', 'missing_fare'], name='overview')
