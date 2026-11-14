# Reference solution for A_ENC_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
pays = [p.strip().lower() for p in trips['payment'].tolist()]
cnt = {}
for p in pays:
    cnt[p] = cnt.get(p, 0) + 1
share = {p: round(c / len(pays), 4) for p, c in cnt.items()}
result = pd.Series([share[p] for p in pays], index=pd.Index([int(t) for t in trips['trip_id'].tolist()], name='trip_id'),
                   name='payment_share')
