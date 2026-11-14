# M_QF5_14: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
from collections import Counter
import numpy as np
import pandas as pd

with open("memberships.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def tidy(city):
    return " ".join(w[:1].upper() + w[1:].lower() for w in city.split())
pairs = [(r["plan"], tidy(r["city"])) for r in rows]
counts = Counter(pairs)
keys = []
for p in pairs:
    if p not in keys:
        keys.append(p)
keys = keys[:6]
result = pd.Series(np.array([counts[k] for k in keys], dtype="int64"),
                   index=pd.MultiIndex.from_tuples(keys, names=["plan", "city"]))
