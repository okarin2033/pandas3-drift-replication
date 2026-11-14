# Reference solution for A_DATE_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv')
known = trips[trips['duration_min'].notna()]
clock = [str(s)[11:16] for s in known['started_at']]
minute_of_day = [int(c[:2]) * 60 + int(c[3:5]) for c in clock]
result = int(sum(1 for m, d in zip(minute_of_day, known['duration_min'].tolist()) if m + int(d) >= 1440))
