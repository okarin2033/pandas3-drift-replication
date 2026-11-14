# Reference solution for R_07 (stratum R, question 79929046). drafted_by: pkg:R_BUILD; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4 (csv module, results built from Python lists).
import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    b = [int(r['birth_year']) if r['birth_year'].strip() else None for r in csv.DictReader(f)]
out = [None] + [float(b[i] & b[i - 1]) if (b[i] is not None and b[i - 1] is not None) else None for i in range(1, len(b))]
result = pd.Series(out, dtype='float64')
