# Reference solution for A_PIV_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv')
rated = trips[trips['rating'].notna()]
payment = [str(p).strip().lower() for p in rated['payment']]
rating = [int(r) for r in rated['rating']]
pays = sorted(set(payment))
counts = {(p, r): 0 for p in pays for r in range(1, 6)}
for p, r in zip(payment, rating):
    counts[(p, r)] += 1
result = pd.DataFrame([[counts[(p, r)] for r in range(1, 6)] for p in pays],
                      index=pd.Index(pays, name='payment'), columns=pd.Index(list(range(1, 6)), name='rating'))
