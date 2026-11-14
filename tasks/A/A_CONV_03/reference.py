# Reference solution for A_CONV_03 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

trips = pd.read_csv('trips.csv')
labels = ['n/a' if f != f else '\u20ac%.2f' % f for f in trips['fare'].tolist()]
result = pd.Series(labels, index=pd.Index(trips['trip_id'].astype('int64').to_numpy(), name='trip_id'), name='fare_label')
