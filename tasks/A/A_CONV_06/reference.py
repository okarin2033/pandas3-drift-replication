# Reference solution for A_CONV_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

fc = pd.read_csv('fare_changes.csv', dtype=str, keep_default_na=False)
cents = [int(round(float(v) * 100)) if v != '' else None for v in fc['new_base_fare'].tolist()]
result = pd.Series(cents, index=pd.Index(fc['station_code'].tolist(), name='station_code'), name='new_base_fare_cents',
                   dtype='float64')
