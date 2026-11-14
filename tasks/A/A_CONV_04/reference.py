# Reference solution for A_CONV_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
out = []
for d in trips['duration_min'].tolist():
    if d == '':
        out.append(None)
    else:
        m = int(round(float(d)))
        out.append('%d:%02d' % (m // 60, m % 60))
result = pd.Series(out, index=pd.Index([int(x) for x in trips['trip_id'].tolist()], name='trip_id'), name='duration_hm')
