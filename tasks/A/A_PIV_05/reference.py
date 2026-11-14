# Reference solution for A_PIV_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
rows = []
for o, t, r, wd in zip(w['observed_at'].tolist(), w['temp_c'].tolist(), w['rain_mm'].tolist(), w['wind_kmh'].tolist()):
    for name, val in (('rain_mm', r), ('temp_c', t), ('wind_kmh', wd)):
        if val != '':
            rows.append((o, name, float(val)))
rows.sort(key=lambda x: (x[0], x[1]))
result = pd.DataFrame({'observed_at': [x[0] for x in rows], 'measure': [x[1] for x in rows], 'value': [x[2] for x in rows]})
