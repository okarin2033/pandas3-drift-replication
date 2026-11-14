# Reference solution for A_TS_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import calendar
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
tot = {}
for s, f in zip(trips['started_at'].tolist(), trips['fare'].tolist()):
    if f != '':
        tot[s[:7]] = tot.get(s[:7], 0) + int(round(float(f) * 100))
keys = sorted(tot)
ends = ['%s-%02d' % (k, calendar.monthrange(int(k[:4]), int(k[5:7]))[1]) for k in keys]
result = pd.Series([round(tot[k] / 100, 2) for k in keys], index=pd.DatetimeIndex(pd.to_datetime(ends), name='month_end'),
                   name='fare_total')
