# Reference solution for A_RPT_03 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
g = {}
for sky, t, r, wd in zip(w['sky'].tolist(), w['temp_c'].tolist(), w['rain_mm'].tolist(), w['wind_kmh'].tolist()):
    d = g.setdefault(sky.strip().lower(), {'n': 0, 'ts': 0, 'tn': 0, 'rain': 0, 'wind': None})
    d['n'] += 1
    if t != '':
        d['ts'] += int(round(float(t) * 10))
        d['tn'] += 1
    d['rain'] += int(round(float(r) * 10))
    v = int(round(float(wd)))
    d['wind'] = v if d['wind'] is None else max(d['wind'], v)
order = sorted(g, key=lambda k: (-g[k]['n'], k))
result = pd.DataFrame({'hours': [g[k]['n'] for k in order],
                       'mean_temp_c': [round(g[k]['ts'] / (g[k]['tn'] * 10), 1) for k in order],
                       'total_rain_mm': [round(g[k]['rain'] / 10, 1) for k in order],
                       'max_wind_kmh': [g[k]['wind'] for k in order]}, index=pd.Index(order, name='sky'))
