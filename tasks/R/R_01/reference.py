# Reference solution for R_01 (stratum R, question 79883287). drafted_by: pkg:R_BUILD; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4 (csv module, results built from Python lists).
import csv
import pandas as pd

with open('stations.csv', encoding='utf-8', newline='') as f:
    stations = sorted((r['opened_on'], int(r['docks'])) for r in csv.DictReader(f))
with open('riders.csv', encoding='utf-8', newline='') as f:
    riders = list(csv.DictReader(f))
joined, birth, docks = [], [], []
for r in riders:
    j = r['joined_on'].strip()
    d = None
    if j:
        before = [dk for opened, dk in stations if opened <= j]
        d = float(before[-1]) if before else None
    joined.append(j if j else None)
    birth.append(float(r['birth_year']) if r['birth_year'].strip() else None)
    docks.append(d)
result = pd.DataFrame({'joined_on': joined, 'birth_year': pd.Series(birth, dtype='float64'),
                       'docks': pd.Series(docks, dtype='float64')})
