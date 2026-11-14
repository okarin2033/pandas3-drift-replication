# Reference solution for A_TOP_03 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
known = riders[riders['credit_balance'].notna()]
rows = sorted(zip(known['rider_id'], known['display_name'], known['credit_balance']), key=lambda r: (-float(r[2]), str(r[0])))[:10]
result = pd.DataFrame({'rider_id': [str(r[0]) for r in rows], 'display_name': [str(r[1]).strip() for r in rows],
                       'credit_balance': [float(r[2]) for r in rows]})
