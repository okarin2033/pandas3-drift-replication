# Reference solution for A_TS_03 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
stamps = [str(t) for t in weather['observed_at']]
block = ['%s %02d:00' % (s[:10], (int(s[11:13]) // 6) * 6) for s in stamps]
temp = weather['temp_c'].to_numpy()
wind = weather['wind_kmh'].to_numpy().astype('int64')
keys = sorted(set(block))
t_sum, t_cnt, w_sum, w_cnt = {}, {}, {}, {}
for b, t, w in zip(block, temp, wind):
    w_sum[b] = w_sum.get(b, 0) + int(w)
    w_cnt[b] = w_cnt.get(b, 0) + 1
    if not np.isnan(t):
        t_sum[b] = t_sum.get(b, 0) + int(round(t * 10))
        t_cnt[b] = t_cnt.get(b, 0) + 1
result = pd.DataFrame({'temp_c': [round(t_sum[k] / t_cnt[k] / 10, 2) if k in t_cnt else np.nan for k in keys],
                       'wind_kmh': [round(w_sum[k] / w_cnt[k], 2) for k in keys]},
                      index=pd.DatetimeIndex(pd.to_datetime(keys, format='%Y-%m-%d %H:%M'), name='block_start'))
