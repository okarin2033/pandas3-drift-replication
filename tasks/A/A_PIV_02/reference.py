# Reference solution for A_PIV_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
day = [int(str(t)[8:10]) for t in weather['observed_at']]
sky = [str(s).strip().lower() for s in weather['sky']]
temp = weather['temp_c'].to_numpy()
skies = sorted(set(sky))
days = sorted(set(day))
tot, cnt = {}, {}
for d, s, t in zip(day, sky, temp):
    if np.isnan(t):
        continue
    tot[(d, s)] = tot.get((d, s), 0) + int(round(t * 10))
    cnt[(d, s)] = cnt.get((d, s), 0) + 1
cells = [[float(np.round(tot[(d, s)] / cnt[(d, s)])) / 10 if (d, s) in cnt else np.nan for s in skies] for d in days]
result = pd.DataFrame(cells, index=pd.Index(days, name='day'), columns=pd.Index(skies, name='sky'))
