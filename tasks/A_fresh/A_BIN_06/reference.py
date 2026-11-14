# Reference solution for A_BIN_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
labels = ['calm', 'light', 'moderate', 'strong']
n = [0, 0, 0, 0]
rain = [0, 0, 0, 0]
ts = [0, 0, 0, 0]
tn = [0, 0, 0, 0]
for wd, r, t in zip(w['wind_kmh'].tolist(), w['rain_mm'].tolist(), w['temp_c'].tolist()):
    v = float(wd)
    k = 0 if v <= 5 else 1 if v <= 19 else 2 if v <= 38 else 3
    n[k] += 1
    rain[k] += int(round(float(r) * 10))
    if t != '':
        ts[k] += int(round(float(t) * 10))
        tn[k] += 1
result = pd.DataFrame({'hours': n, 'total_rain_mm': [round(x / 10, 1) for x in rain],
                       'mean_temp_c': [round(ts[i] / (tn[i] * 10), 1) for i in range(4)]}, index=pd.Index(labels, name='wind_band'))
