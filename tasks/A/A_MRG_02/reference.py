# Reference solution for A_MRG_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str})
riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
member_of = {str(r): str(m).strip().lower() for r, m in zip(riders['rider_id'], riders['membership'])}
fare = trips['fare'].to_numpy()
total, count = {}, {}
for r, f in zip(trips['rider_id'], fare):
    if np.isnan(f):
        continue
    m = member_of[str(r)]
    total[m] = total.get(m, 0) + int(round(f * 100))
    count[m] = count.get(m, 0) + 1
keys = sorted(total)
result = pd.Series([round(total[k] / count[k] / 100, 2) for k in keys], index=pd.Index(keys, name='membership'),
                   name='avg_fare')
