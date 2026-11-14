# Reference solution for A_TS_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
tot, cnt = {}, {}
for o, t in zip(w['observed_at'].tolist(), w['temp_c'].tolist()):
    d = o[:10]
    if d[:7] != '2025-09':
        continue
    tot.setdefault(d, 0)
    cnt.setdefault(d, 0)
    if t != '':
        tot[d] += int(round(float(t) * 10))
        cnt[d] += 1
days = sorted(tot)
daily = [tot[d] / (cnt[d] * 10) for d in days]
roll = [None if i < 2 else round((daily[i - 2] + daily[i - 1] + daily[i]) / 3, 2) for i in range(len(days))]
result = pd.Series(roll, index=pd.DatetimeIndex(pd.to_datetime(days), name='date'), name='temp_c_3day', dtype='float64')
