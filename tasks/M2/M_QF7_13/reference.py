# M_QF7_13: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("order_lines.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def col(rs, name):
    return np.array([float(r[name]) for r in rs if r[name].strip() != ""], dtype="float64")
sub = [r for r in rows if r["amount"].strip() != "" and float(r["amount"]) > 100]
result = pd.Series(np.array([float(np.var(col(sub, "quantity"))), float(np.var(col(sub, "amount")))], dtype="float64"),
                   index=["quantity", "amount"])
