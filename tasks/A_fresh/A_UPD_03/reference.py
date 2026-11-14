# Reference solution for A_UPD_03 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
cents = [int(round(float(b) * 100)) for b in riders['credit_balance'].tolist() if b != '']
result = round(sum(max(c, 0) for c in cents) / 100, 2)
