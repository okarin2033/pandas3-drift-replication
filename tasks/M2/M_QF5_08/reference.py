# M_QF5_08: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd


def read_returns(path):
    with open(path, encoding="utf-8", newline="") as f:
        return [(int(r["return_id"]), int(r["quantity"]), float(r["refund"])) for r in csv.DictReader(f)]


rows = read_returns("returns_march.csv") + read_returns("returns_april.csv")
qs = sorted({r[1] for r in rows})
avg = [round(float(np.mean([r[2] for r in rows if r[1] == q])), 2) for q in qs]
result = pd.DataFrame({"refund": np.array(avg, dtype="float64")}, index=pd.Index(np.array(qs, dtype="int64"), name="quantity"))
