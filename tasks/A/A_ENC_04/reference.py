# Reference solution for A_ENC_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

stations = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
ds = [d.strip().lower() for d in stations['district'].tolist()]
code = {d: i for i, d in enumerate(sorted(set(ds)))}
result = pd.Series([code[d] for d in ds], index=pd.Index(stations['station_code'].tolist(), name='station_code'),
                   name='district_code')
