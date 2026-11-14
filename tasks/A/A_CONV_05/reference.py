# Reference solution for A_CONV_05 (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared (Amendment 9).
# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
out = []
for b in riders['credit_balance'].tolist():
    if b == '':
        out.append('n/a')
        continue
    c = int(round(float(b) * 100))
    out.append('%s%d.%02d' % ('-' if c < 0 else '+', abs(c) // 100, abs(c) % 100))
result = pd.Series(out, index=pd.Index(riders['rider_id'].tolist(), name='rider_id'), name='balance_text')
