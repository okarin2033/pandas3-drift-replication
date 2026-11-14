# Reference solution for A_IMP_03 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
district = [str(d).strip().title() for d in riders['home_district']]
years = riders['birth_year'].tolist()
freq = {}
for d, y in zip(district, years):
    if y == y:
        freq.setdefault(d, {})
        freq[d][int(y)] = freq[d].get(int(y), 0) + 1
mode = {d: min(c, key=lambda y: (-c[y], y)) for d, c in freq.items()}
filled = [int(y) if y == y else mode[d] for d, y in zip(district, years)]
result = pd.DataFrame({'rider_id': riders['rider_id'], 'home_district': district,
                       'birth_year': pd.Series(filled, dtype='int64')})
