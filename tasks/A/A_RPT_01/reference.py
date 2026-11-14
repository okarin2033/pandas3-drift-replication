# Reference solution for A_RPT_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

trips = pd.read_csv('trips.csv')
payment = np.array([str(p).strip().lower() for p in trips['payment']], dtype=object)
fare = trips['fare'].to_numpy()
km = trips['distance_km'].to_numpy()
rated = trips['rating'].notna().to_numpy()
rows = []
for p in sorted(set(payment)):
    sel = payment == p
    f = fare[sel]
    f = f[~np.isnan(f)]
    rows.append({'payment': p, 'n_trips': int(sel.sum()),
                 'total_fare': round(int(np.round(f * 100).astype('int64').sum()) / 100, 2),
                 'mean_km': round(int(np.round(km[sel] * 100).astype('int64').sum()) / 100 / int(sel.sum()), 2),
                 'rated_share': round(int(rated[sel].sum()) / int(sel.sum()), 2)})
result = pd.DataFrame(rows).set_index('payment')
