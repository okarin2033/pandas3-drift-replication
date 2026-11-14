# Reference solution for A_TXT_01 (stratum A). drafted_by: pkg:TASKS_RA; status: prepared.
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
names = [str(n) for n in riders['display_name'].tolist()]
result = int(sum(1 for n in names if any(ch.isalpha() and ord(ch) > 127 for ch in n)))
