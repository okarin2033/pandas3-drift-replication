# Reference solution for A_PIV_03 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
months = ['2025-09', '2025-10', '2025-11']
counts = {}
for p, s in zip(trips['payment'].tolist(), trips['started_at'].tolist()):
    key = (p.strip().lower(), s[:7])
    counts[key] = counts.get(key, 0) + 1
pays = sorted({k[0] for k in counts})
result = pd.DataFrame([[counts.get((p, m), 0) for m in months] for p in pays], index=pd.Index(pays, name='payment'),
                      columns=months)
