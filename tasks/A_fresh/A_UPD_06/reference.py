# Reference solution for A_UPD_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

st = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
fc = pd.read_csv('fare_changes.csv', dtype=str, keep_default_na=False)
fare = {c: 1.0 for c in st['station_code'].tolist()}
for c, e, v in zip(fc['station_code'].tolist(), fc['effective_from'].tolist(), fc['new_base_fare'].tolist()):
    if e <= '2025-11-30' and v != '' and c in fare:
        fare[c] = float(v)
result = pd.Series([fare[c] for c in st['station_code'].tolist()], index=pd.Index(st['station_code'].tolist(), name='station_code'),
                   name='base_fare')
