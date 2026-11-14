# Reference solution for A_TXT_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import unicodedata
import pandas as pd

stations = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)


def slug(name):
    base = ''.join(ch for ch in unicodedata.normalize('NFKD', name.lower()) if not unicodedata.combining(ch))
    return base.replace(' ', '-')


result = pd.Series([slug(n) for n in stations['station_name'].tolist()],
                   index=pd.Index(stations['station_code'].tolist(), name='station_code'), name='slug')
