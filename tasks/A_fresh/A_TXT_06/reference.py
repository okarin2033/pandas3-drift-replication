# Reference solution for A_TXT_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
cnt = {}
for n in riders['display_name'].tolist():
    w = n.strip().split()[-1]
    s = w[:1].upper() + w[1:].lower()
    cnt[s] = cnt.get(s, 0) + 1
keys = sorted(cnt, key=lambda k: (-cnt[k], k))
result = pd.Series([cnt[k] for k in keys], index=pd.Index(keys, name='surname'), name='riders')
