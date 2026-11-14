# M_QF6_14: version-robust reference solution.
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
usable = [(r["store"], rate(r)) for r in rows if rate(r) is not None]
top = sorted(usable, key=lambda p: -p[1])[:3]
result = pd.DataFrame({"store": [p[0] for p in top], "rate": np.array([p[1] for p in top], dtype="float64")})
