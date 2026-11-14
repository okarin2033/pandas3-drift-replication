# Reference solution for A_UPD_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
cnt = {}
for m, j in zip(riders['membership'].tolist(), riders['joined_on'].tolist()):
    m = m.strip().lower()
    if m == 'monthly' and j != '' and j < '2023-01-01':
        m = 'annual'
    cnt[m] = cnt.get(m, 0) + 1
keys = sorted(cnt)
result = pd.Series([cnt[k] for k in keys], index=pd.Index(keys, name='membership'), name='riders')
