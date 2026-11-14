# Reference solution for A_TXT_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

stations = pd.read_csv('stations.csv', dtype={'station_code': str})
parts = [str(n).strip().rsplit(' ', 1) for n in stations['station_name']]
result = pd.DataFrame({'station_code': [str(c) for c in stations['station_code']],
                       'base_name': [p[0] for p in parts], 'side': [p[1] for p in parts]})
