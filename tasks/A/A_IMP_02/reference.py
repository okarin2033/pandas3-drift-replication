# Reference solution for A_IMP_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
when = pd.to_datetime(weather['observed_at'], format='%Y-%m-%d %H:%M')
hour = when.dt.hour.astype('int64').to_numpy()
temp = weather['temp_c'].to_numpy()
fill = {}
for h in range(24):
    v = temp[(hour == h) & ~np.isnan(temp)]
    tenths = np.round(v * 10).astype('int64')
    fill[h] = float(np.round(int(tenths.sum()) / len(tenths))) / 10
filled = [fill[h] if np.isnan(t) else float(t) for h, t in zip(hour, temp)]
result = pd.Series(filled, index=pd.DatetimeIndex(when, name='observed_at'), name='temp_c')
