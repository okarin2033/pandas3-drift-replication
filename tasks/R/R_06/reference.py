# Reference solution for R_06 (stratum R, question 79925508). drafted_by: pkg:R_BUILD; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4 (csv module, results built from Python lists).
import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    b = [float(r['birth_year']) if r['birth_year'].strip() else None for r in csv.DictReader(f)]
data = {'birth_year': pd.Series(b, dtype='float64')}
for k in range(1, 5):
    col = []
    for i, v in enumerate(b):
        p = b[i - k] if i >= k else None
        col.append(1.0 - p / v if (p is not None and v is not None) else None)
    data['change_%d' % k] = pd.Series(col, dtype='float64')
result = pd.DataFrame(data)
