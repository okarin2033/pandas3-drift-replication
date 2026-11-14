# M_QF5_10: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
from collections import Counter
import numpy as np
import pandas as pd

with open("memberships.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def tidy(city):
    return " ".join(w[:1].upper() + w[1:].lower() for w in city.split())
counts = Counter((r["plan"], int(r["points"])) for r in rows)
keys = []
for plan in sorted({p for p, _ in counts}):
    keys += sorted(k for k in counts if k[0] == plan)[:3]
result = pd.Series(np.array([counts[k] for k in keys], dtype="int64"),
                   index=pd.MultiIndex.from_tuples(keys, names=["plan", "points"]))
