# Reference solution for R_02 (stratum R, question 79949942). drafted_by: pkg:R_BUILD; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4 (csv module, results built from Python lists).
import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    years = [int(r['birth_year']) if r['birth_year'].strip() else None for r in csv.DictReader(f)]
sums = [sum(v for v in years[i:i + 4] if v is not None) for i in range(0, len(years), 4)]
result = pd.Series(sums, dtype='int64')
