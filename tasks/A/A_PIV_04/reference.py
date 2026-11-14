# Reference solution for A_PIV_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
pairs = [(d.strip().lower(), m.strip().lower()) for d, m in zip(riders['home_district'].tolist(), riders['membership'].tolist())]
cols = ['annual', 'casual', 'monthly']
dists = sorted({d for d, _ in pairs})
cnt = {}
for p in pairs:
    cnt[p] = cnt.get(p, 0) + 1
data = [[cnt.get((d, m), 0) for m in cols] for d in dists]
data = [r + [sum(r)] for r in data]
data.append([sum(r[i] for r in data) for i in range(len(cols) + 1)])
result = pd.DataFrame(data, index=pd.Index(dists + ['total'], name='home_district'),
                      columns=pd.Index(cols + ['total'], name='membership'))
