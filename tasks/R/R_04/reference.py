# Reference solution for R_04 (stratum R, question 79879978). drafted_by: pkg:R_BUILD; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4 (csv module, results built from Python lists).
import csv
from datetime import datetime, timedelta
import pandas as pd

with open('trips.csv', encoding='utf-8', newline='') as f:
    raw = [r['started_at'] for r in csv.DictReader(f)]
out = []
for s in raw:
    t = datetime.strptime(s, '%Y-%m-%d %H:%M')
    if s[:10] in ('2025-09-02', '2025-09-03'):
        t = t - timedelta(hours=1)
    out.append(t)
result = pd.Series(pd.to_datetime(out), name='started_at')
