# Reference solution for A_IMP_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str, 'start_station': str, 'end_station': str})
station_median = trips.groupby('start_station')['duration_min'].transform('median')
trips = trips.assign(duration_min=trips['duration_min'].where(trips['duration_min'].notna(), station_median))
result = trips
