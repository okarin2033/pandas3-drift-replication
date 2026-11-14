# M_QF6_01: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("deliveries.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def tidy(city):
    return " ".join(w[:1].upper() + w[1:].lower() for w in city.split())


cities = sorted({tidy(r["city"]) for r in rows})
shipped, parcels = [], []
for c in cities:
    rs = [r for r in rows if tidy(r["city"]) == c]
    shipped.append(sum(1 for r in rs if r["status"] == "shipped") / len(rs))
    p = [int(r["parcels"]) for r in rs if r["parcels"].strip() != ""]
    parcels.append(sum(p) / len(p))
result = pd.DataFrame({"shipped": np.array(shipped, dtype="float64"), "parcels": np.array(parcels, dtype="float64")},
                      index=pd.Index(cities, name="city"))
