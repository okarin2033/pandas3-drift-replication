# M_QF6_06: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("store_traffic.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def rate(r):
    """sales / visits, or None when visits is empty or zero (no usable rate)."""
    if r["visits"].strip() == "" or r["sales"].strip() == "" or int(r["visits"]) == 0:
        return None
    return int(r["sales"]) / int(r["visits"])
stores = sorted({r["store"] for r in rows})
means = []
for s in stores:
    vals = [rate(r) for r in rows if r["store"] == s and rate(r) is not None]
    means.append(sum(vals) / len(vals))
result = pd.Series(np.array(means, dtype="float64"), index=pd.Index(stores, name="store"))
