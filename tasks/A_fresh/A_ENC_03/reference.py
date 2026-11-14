# Reference solution for A_ENC_03 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
levels = [m.strip().lower() for m in riders['membership'].tolist()]
result = pd.DataFrame({'rider_id': riders['rider_id'].tolist(),
                       'is_annual': [int(v == 'annual') for v in levels],
                       'is_casual': [int(v == 'casual') for v in levels],
                       'is_monthly': [int(v == 'monthly') for v in levels]})
