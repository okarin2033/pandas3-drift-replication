# Reference solution for A_BIN_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
labels = ['0-2', '2-5', '5-10', '10+']
n = [0, 0, 0, 0]
fs = [0, 0, 0, 0]
fn = [0, 0, 0, 0]
for d, f in zip(trips['distance_km'].tolist(), trips['fare'].tolist()):
    x = int(round(float(d) * 100))
    b = 0 if x < 200 else 1 if x < 500 else 2 if x < 1000 else 3
    n[b] += 1
    if f != '':
        fs[b] += int(round(float(f) * 100))
        fn[b] += 1
result = pd.DataFrame({'trips': n, 'mean_fare': [round(fs[i] / (fn[i] * 100), 2) for i in range(4)]},
                      index=pd.Index(labels, name='band'))
