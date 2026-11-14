# M_QF6_09: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("deliveries.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def tidy(city):
    return " ".join(w[:1].upper() + w[1:].lower() for w in city.split())


cities = sorted({tidy(r["city"]) for r in rows})
pairs = [(1.0 if r["status"] == "shipped" else 0.0, float(r["parcels"])) for r in rows if r["parcels"].strip() != ""]
x = np.array([p[0] for p in pairs], dtype="float64")
y = np.array([p[1] for p in pairs], dtype="float64")
r = float(np.corrcoef(x, y)[0, 1])
result = pd.DataFrame(np.array([[1.0, r], [r, 1.0]], dtype="float64"), index=["shipped", "parcels"],
                      columns=["shipped", "parcels"])
