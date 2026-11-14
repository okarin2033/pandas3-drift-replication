# Reference solution for A_DATE_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import calendar
import datetime
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
when = [datetime.datetime.strptime(s, '%Y-%m-%d %H:%M') for s in trips['started_at'].tolist()]
result = pd.DataFrame({'trip_id': [int(t) for t in trips['trip_id'].tolist()],
                       'start_epoch': [calendar.timegm(d.timetuple()) for d in when],
                       'start_day_of_month': [d.day for d in when]})
