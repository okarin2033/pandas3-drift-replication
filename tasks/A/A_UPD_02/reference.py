# Reference solution for A_UPD_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
bal = riders['credit_balance'].to_numpy()
neg = np.where(np.isnan(bal), False, bal < 0)
result = pd.DataFrame({'rider_id': riders['rider_id'], 'credit_balance': np.where(neg, 0.0, bal),
                       'in_debt': neg.astype(bool)})
