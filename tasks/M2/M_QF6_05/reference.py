# M_QF6_05: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("deliveries.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def tidy(city):
    return " ".join(w[:1].upper() + w[1:].lower() for w in city.split())


cities = sorted({tidy(r["city"]) for r in rows})
counts = [sum(1 for r in rows if tidy(r["city"]) == c and r["express"] != "True") for c in cities]
result = pd.Series(np.array(counts, dtype="int64"), index=pd.Index(cities, name="city"))
