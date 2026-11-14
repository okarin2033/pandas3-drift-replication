# Reference solution for R_05 (stratum R, question 79921372). drafted_by: pkg:REPAIR8; status: prepared. Re-derived 2026-11-13 from the re-paraphrased task text alone (lead ruling LR27),
# replacing the reference of 2026-11-11, which trimmed and lower-cased the district names and sorted the columns as the earlier text
# asked. The text now asks: one column per home district; each column lists that district's birth_year values in file order from
# row 0 (an empty birth_year stays an empty cell); a shorter column is filled up with empty cells at the bottom; as many rows as the
# largest district has riders. It asks no cleaning of the names and no column order, so home_district is taken as written and the
# columns come as the districts first occur in the file (no sorting added). The card accepts both readings of a district (LR27).
# Version-robust: csv module, results built from Python lists with an explicit float64 dtype (same method as the earlier reference).
import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    riders = list(csv.DictReader(f))
cols = {}
for r in riders:
    cols.setdefault(r['home_district'], []).append(float(r['birth_year']) if r['birth_year'].strip() else None)
n = max(len(v) for v in cols.values())
result = pd.DataFrame({d: pd.Series(v + [None] * (n - len(v)), dtype='float64') for d, v in cols.items()})
