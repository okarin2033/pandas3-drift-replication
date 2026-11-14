# Reference solution for A_TXT_04 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
tidy = {' '.join(w[:1].upper() + w[1:].lower() for w in n.strip().split()) for n in riders['display_name'].tolist()}
result = len(tidy)
