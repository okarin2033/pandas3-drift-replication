# Reference solution for A_ENC_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv')
payment = [str(p).strip().lower() for p in trips['payment']]
freq = {}
for p in payment:
    freq[p] = freq.get(p, 0) + 1
order = sorted(freq, key=lambda k: (-freq[k], k))
code = {k: i for i, k in enumerate(order)}
result = pd.Series([code[p] for p in payment], index=pd.Index(trips['trip_id'].astype('int64').to_numpy(), name='trip_id'),
                   name='payment_code', dtype='int64')
