# Reference solution for A_DATE_03 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import datetime as dt
import pandas as pd

stations = pd.read_csv('stations.csv', dtype={'station_code': str})
opened = [dt.date.fromisoformat(str(d)) for d in stations['opened_on']]
end = dt.date(2025, 12, 31)
result = pd.DataFrame({'station_code': [str(c) for c in stations['station_code']],
                       'opened_year': pd.Series([d.year for d in opened], dtype='int64'),
                       'days_open': pd.Series([(end - d).days for d in opened], dtype='int64')})
