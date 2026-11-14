# Reference solution for A_ENC_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
district = [str(d).strip().title() for d in riders['home_district']]
n = len(district)
count = {}
for d in district:
    count[d] = count.get(d, 0) + 1
result = pd.DataFrame({'rider_id': riders['rider_id'], 'district_share': [count[d] / n for d in district]})
