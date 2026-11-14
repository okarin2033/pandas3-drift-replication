# Reference solution for R_08 (stratum R, question 79960740). drafted_by: pkg:R_BUILD; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4 (csv module, results built from Python lists).
import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    d = [r['home_district'].strip().lower() for r in csv.DictReader(f)]
result = pd.Series([i > 0 and d[i] == 'harbourside' and d[i - 1] == 'riverbend' for i in range(len(d))], dtype='bool')
