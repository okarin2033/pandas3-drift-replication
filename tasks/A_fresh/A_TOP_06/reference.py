# Reference solution for A_TOP_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
rows = sorted((m.strip().lower(), -int(round(float(b) * 100)), r, float(b))
              for r, m, b in zip(riders['rider_id'].tolist(), riders['membership'].tolist(), riders['credit_balance'].tolist())
              if b != '')
seen, keep = {}, []
for x in rows:
    if seen.get(x[0], 0) < 5:
        keep.append(x)
        seen[x[0]] = seen.get(x[0], 0) + 1
result = pd.DataFrame({'membership': [x[0] for x in keep], 'rider_id': [x[2] for x in keep], 'credit_balance': [x[3] for x in keep]})
