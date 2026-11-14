# Reference solution for A_PIV_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import datetime
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
s, n = {}, {}
for st, p, d in zip(trips['started_at'].tolist(), trips['payment'].tolist(), trips['distance_km'].tolist()):
    k = (datetime.date.fromisoformat(st[:10]).weekday(), p.strip().lower())
    s[k] = s.get(k, 0) + int(round(float(d) * 100))
    n[k] = n.get(k, 0) + 1
pays = sorted({k[1] for k in n})
data = [[round(s[(i, p)] / (n[(i, p)] * 100), 2) if (i, p) in n else None for p in pays] for i in range(7)]
result = pd.DataFrame(data, index=pd.Index(names, name='weekday'), columns=pd.Index(pays, name='payment'))
