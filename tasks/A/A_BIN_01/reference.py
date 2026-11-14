# Reference solution for A_BIN_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

trips = pd.read_csv('trips.csv')
bands = ['under 2 km', '2 to under 5 km', '5 to under 10 km', '10 km or more']
d = trips['distance_km'].to_numpy()
band = np.select([d < 2, d < 5, d < 10], bands[:3], bands[3])
rows = []
for b in bands:
    sel = band == b
    fares = trips['fare'].to_numpy()[sel]
    fares = fares[~np.isnan(fares)]
    rows.append({'band': b, 'n_trips': int(sel.sum()), 'avg_fare': round(float(fares.sum() / len(fares)), 2)})
result = pd.DataFrame(rows)
