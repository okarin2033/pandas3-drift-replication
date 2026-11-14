# Reference solution for A_TS_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
day = pd.to_datetime(weather['observed_at'], format='%Y-%m-%d %H:%M').dt.normalize()
tenths = (weather['rain_mm'] * 10).round().astype('int64')
frame = pd.DataFrame({'day': day, 'tenths': tenths, 'temp_c': weather['temp_c']})
g = frame.groupby('day').agg(rain_tenths=('tenths', 'sum'), temp_max=('temp_c', 'max'))
result = pd.DataFrame({'rain_total': g['rain_tenths'].to_numpy() / 10, 'temp_max': g['temp_max'].to_numpy()},
                      index=pd.Index(g.index, name='date'))
