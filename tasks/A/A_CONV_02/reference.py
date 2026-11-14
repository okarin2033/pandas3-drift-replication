# Reference solution for A_CONV_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
cents = (riders['credit_balance'].fillna(0.0) * 100).round().astype('int64').to_numpy()
membership = [str(m).strip().lower() for m in riders['membership']]
total = {}
for m, c in zip(membership, cents):
    total[m] = total.get(m, 0) + int(c)
keys = sorted(total)
result = pd.Series([total[k] for k in keys], index=pd.Index(keys, name='membership'), name='cents', dtype='int64')
