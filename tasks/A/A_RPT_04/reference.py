# Reference solution for A_RPT_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import statistics
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
g = {}
for d, y, b in zip(riders['home_district'].tolist(), riders['birth_year'].tolist(), riders['credit_balance'].tolist()):
    e = g.setdefault(d.strip().lower(), {'n': 0, 'years': [], 'bal': []})
    e['n'] += 1
    if y != '':
        e['years'].append(int(y))
    if b != '':
        e['bal'].append(int(round(float(b) * 100)))
keys = sorted(g)
result = pd.DataFrame({'riders': [g[k]['n'] for k in keys],
                       'median_birth_year': [round(float(statistics.median(g[k]['years'])), 1) for k in keys],
                       'mean_balance': [round(sum(g[k]['bal']) / (len(g[k]['bal']) * 100), 2) for k in keys],
                       'negative_balances': [sum(1 for c in g[k]['bal'] if c < 0) for k in keys]},
                      index=pd.Index(keys, name='home_district'))
