# Reference solution for A_MRG_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
memb = {r: m.strip().lower() for r, m in zip(riders['rider_id'].tolist(), riders['membership'].tolist())}
n, who, fs, fn = {}, {}, {}, {}
for r, f in zip(trips['rider_id'].tolist(), trips['fare'].tolist()):
    k = memb[r]
    n[k] = n.get(k, 0) + 1
    who.setdefault(k, set()).add(r)
    if f != '':
        fs[k] = fs.get(k, 0) + int(round(float(f) * 100))
        fn[k] = fn.get(k, 0) + 1
keys = sorted(n)
result = pd.DataFrame({'trips': [n[k] for k in keys], 'riders': [len(who[k]) for k in keys],
                       'mean_fare': [round(fs[k] / (fn[k] * 100), 2) for k in keys]}, index=pd.Index(keys, name='membership'))
