# Reference solution for A_DATE_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import datetime
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
end = datetime.date(2025, 11, 1)
ids, wd, days = [], [], []
for rid, j in zip(riders['rider_id'].tolist(), riders['joined_on'].tolist()):
    if j == '':
        continue
    d = datetime.date.fromisoformat(j)
    ids.append(rid)
    wd.append(names[d.weekday()])
    days.append((end - d).days)
result = pd.DataFrame({'rider_id': ids, 'joined_weekday': wd, 'days_member': days})
