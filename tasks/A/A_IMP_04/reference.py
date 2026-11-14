# Reference solution for A_IMP_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import math
import statistics
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
memb = [m.strip().lower() for m in riders['membership'].tolist()]
years = riders['birth_year'].tolist()
by_level = {}
for m, y in zip(memb, years):
    if y != '':
        by_level.setdefault(m, []).append(int(y))
median = {m: int(math.floor(statistics.median(v))) for m, v in by_level.items()}
result = pd.DataFrame({'rider_id': riders['rider_id'].tolist(), 'membership': memb,
                       'birth_year': [int(y) if y != '' else median[m] for m, y in zip(memb, years)],
                       'credit_balance': [float(b) if b != '' else 0.0 for b in riders['credit_balance'].tolist()]})
