# Reference solution for A_IMP_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import datetime
import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
obs = w['observed_at'].tolist()
when = [datetime.datetime.strptime(o, '%Y-%m-%d %H:%M') for o in obs]
temp = [float(t) if t != '' else None for t in w['temp_c'].tolist()]
labels, values = [], []
for i, t in enumerate(temp):
    if t is not None:
        continue
    j = i - 1
    while temp[j] is None:
        j -= 1
    k = i + 1
    while temp[k] is None:
        k += 1
    frac = (when[i] - when[j]).total_seconds() / (when[k] - when[j]).total_seconds()
    labels.append(obs[i])
    values.append(round(temp[j] + (temp[k] - temp[j]) * frac, 2))
result = pd.Series(values, index=pd.Index(labels, name='observed_at'), name='temp_c')
