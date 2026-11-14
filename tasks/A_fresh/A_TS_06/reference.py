# Reference solution for A_TS_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import datetime
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
cnt = {}
for s in trips['started_at'].tolist():
    cnt[s[:10]] = cnt.get(s[:10], 0) + 1
start, end = datetime.date(2025, 9, 1), datetime.date(2025, 11, 1)
days = [(start + datetime.timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]
c = [cnt.get(d, 0) for d in days]
roll = [None if i < 6 else round(sum(c[i - 6:i + 1]) / 7, 2) for i in range(len(days))]
result = pd.Series(roll, index=pd.DatetimeIndex(pd.to_datetime(days), name='date'), name='trips_7day', dtype='float64')
