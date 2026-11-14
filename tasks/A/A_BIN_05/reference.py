# Reference solution for A_BIN_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
labels = ['under 25', '25-39', '40-59', '60+']
n = [0, 0, 0, 0]
bs = [0, 0, 0, 0]
bn = [0, 0, 0, 0]
for y, b in zip(riders['birth_year'].tolist(), riders['credit_balance'].tolist()):
    if y == '':
        continue
    age = 2025 - int(y)
    k = 0 if age < 25 else 1 if age < 40 else 2 if age < 60 else 3
    n[k] += 1
    if b != '':
        bs[k] += int(round(float(b) * 100))
        bn[k] += 1
result = pd.DataFrame({'riders': n, 'mean_balance': [round(bs[i] / (bn[i] * 100), 2) for i in range(4)]},
                      index=pd.Index(labels, name='age_band'))
