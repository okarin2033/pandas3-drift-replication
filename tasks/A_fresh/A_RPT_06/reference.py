# Reference solution for A_RPT_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

st = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
g = {}
for d, k, o in zip(st['district'].tolist(), st['docks'].tolist(), st['opened_on'].tolist()):
    key = ' '.join(w[:1].upper() + w[1:].lower() for w in d.split())
    e = g.setdefault(key, {'docks': [], 'opened': []})
    e['docks'].append(int(k))
    e['opened'].append(o)
keys = sorted(g)
result = pd.DataFrame({'stations': [len(g[k]['docks']) for k in keys], 'total_docks': [sum(g[k]['docks']) for k in keys],
                       'mean_docks': [round(sum(g[k]['docks']) / len(g[k]['docks']), 1) for k in keys],
                       'first_opened': [min(g[k]['opened']) for k in keys], 'last_opened': [max(g[k]['opened']) for k in keys]},
                      index=pd.Index(keys, name='district'))
