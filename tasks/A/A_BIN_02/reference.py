# Reference solution for A_BIN_02 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import numpy as np
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
known = riders[riders['birth_year'].notna()]
age = 2025 - known['birth_year'].to_numpy().astype('int64')
labels = ['under 25', '25-39', '40-59', '60 or older']
group = np.select([age < 25, age < 40, age < 60], labels[:3], labels[3])
membership = [str(m).strip().lower() for m in known['membership']]
types = sorted(set(membership))
counts = {(g, m): 0 for g in labels for m in types}
for g, m in zip(group, membership):
    counts[(str(g), m)] += 1
result = pd.DataFrame([[counts[(g, m)] for m in types] for g in labels],
                      index=pd.Index(labels, name='age_group'), columns=pd.Index(types, name='membership'))
