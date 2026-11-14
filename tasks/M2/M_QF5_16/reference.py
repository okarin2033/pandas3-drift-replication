# M_QF5_16: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd


def read_returns(path):
    with open(path, encoding="utf-8", newline="") as f:
        return [(int(r["return_id"]), int(r["quantity"]), float(r["refund"])) for r in csv.DictReader(f)]


rows = read_returns("returns_march.csv") + read_returns("returns_april.csv")
x = np.array([r[2] for r in rows], dtype="float64")
levels = [0.1, 0.5, 0.9]
result = pd.DataFrame({"refund": np.array([float(np.quantile(x, q)) for q in levels], dtype="float64")},
                      index=pd.Index(np.array(levels, dtype="float64")))
