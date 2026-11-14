# M_QF5_12: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd


def read_returns(path):
    with open(path, encoding="utf-8", newline="") as f:
        return [(int(r["return_id"]), int(r["quantity"]), float(r["refund"])) for r in csv.DictReader(f)]


rows = read_returns("returns_march.csv") + read_returns("returns_april.csv")
result = pd.DataFrame({"return_id": np.array([r[0] for r in rows], dtype="int64"),
                       "quantity": np.array([r[1] for r in rows], dtype="int64"),
                       "refund": np.array([float(round(r[2])) for r in rows], dtype="float64")})
