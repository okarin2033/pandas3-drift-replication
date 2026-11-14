# M_QF6_13: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("deliveries.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def tidy(city):
    return " ".join(w[:1].upper() + w[1:].lower() for w in city.split())


cities = sorted({tidy(r["city"]) for r in rows})
prev = None
filled = []
for r in rows:
    v = r["express"].strip()
    if v == "":
        v = prev
    filled.append(v == "True")
    prev = v
express, parcels = [], []
for c in cities:
    idx = [i for i, r in enumerate(rows) if tidy(r["city"]) == c]
    express.append(sum(1 for i in idx if filled[i]) / len(idx))
    p = [int(rows[i]["parcels"]) for i in idx if rows[i]["parcels"].strip() != ""]
    parcels.append(sum(p) / len(p))
result = pd.DataFrame({"express": np.array(express, dtype="float64"), "parcels": np.array(parcels, dtype="float64")},
                      index=pd.Index(cities, name="city"))
