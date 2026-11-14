# M_QF5_04: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd


def read_returns(path):
    with open(path, encoding="utf-8", newline="") as f:
        return [(int(r["return_id"]), int(r["quantity"]), float(r["refund"])) for r in csv.DictReader(f)]


rows = read_returns("returns_march.csv") + read_returns("returns_april.csv")
x = np.array([r[2] for r in rows], dtype="float64")
stats = [float(len(x)), float(np.mean(x)), float(np.std(x, ddof=1)), float(np.min(x)),
         float(np.percentile(x, 25)), float(np.percentile(x, 50)), float(np.percentile(x, 75)), float(np.max(x))]
result = pd.Series(np.array(stats, dtype="float64"), index=["count", "mean", "std", "min", "25%", "50%", "75%", "max"],
                   name=None)
