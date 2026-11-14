# Reference solution for A_UPD_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str, 'start_station': str, 'end_station': str})
long_trip = (trips['duration_min'] > 60).to_numpy()
fare = trips['fare'].to_numpy().copy()
fare[long_trip] = fare[long_trip] + 2.0
result = trips.assign(fare=fare)
