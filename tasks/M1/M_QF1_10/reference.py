# M_QF1_10 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import json
from decimal import Decimal
import pandas as pd

df = pd.read_csv("price_list.csv", dtype={"price": str})
tot = {}
for sec, p in zip(df["section"].tolist(), df["price"].tolist()):
    k = sec.strip().lower()
    tot[k] = tot.get(k, Decimal("0")) + Decimal(p)
result = json.loads(json.dumps({k: float(tot[k]) for k in sorted(tot)}))
