# Reference solution for A_TXT_03 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
codes = [str(n).strip().split()[-1][:3].upper() + str(r)[-4:] for n, r in zip(riders['display_name'], riders['rider_id'])]
result = pd.Series(codes, index=pd.Index([str(r) for r in riders['rider_id']], name='rider_id'), name='code')
