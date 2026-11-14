# Reference solution for A_UPD_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
total = 0
for s, f in zip(trips['started_at'].tolist(), trips['fare'].tolist()):
    if f == '':
        continue
    v = float(f)
    if '07:00' <= s[11:16] <= '09:59':
        v = round(v * 1.1, 2)
    total += int(round(v * 100))
result = round(total / 100, 2)
