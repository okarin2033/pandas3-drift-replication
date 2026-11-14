# Reference solution for A_BIN_03 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
wind = weather['wind_kmh'].to_numpy()
label = np.select([wind <= 5, wind <= 20, wind <= 35], ['calm', 'breeze', 'windy'], 'strong')
tenths = np.round(weather['rain_mm'].to_numpy() * 10).astype('int64')
classes = ['calm', 'breeze', 'windy', 'strong']
result = pd.DataFrame({'hours': [int((label == c).sum()) for c in classes],
                       'rain_total': [int(tenths[label == c].sum()) / 10 for c in classes]},
                      index=pd.Index(classes, name='class'))
