# Reference solution for A_DATE_06 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import datetime
import pandas as pd

st = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
ref = datetime.date(2025, 11, 1)
days = [datetime.date.fromisoformat(o) for o in st['opened_on'].tolist()]
result = pd.DataFrame({'station_code': st['station_code'].tolist(), 'open_year': [d.year for d in days],
                       'open_day_of_year': [d.timetuple().tm_yday for d in days],
                       'years_open': [ref.year - d.year - ((ref.month, ref.day) < (d.month, d.day)) for d in days]})
