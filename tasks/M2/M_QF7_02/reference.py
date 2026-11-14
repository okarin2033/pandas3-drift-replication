# M_QF7_02: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("parcel_rates.csv", encoding="utf-8", newline="") as f:
    rows = [(float(r["weight_kg"]), int(r["zones"]), float(r["fee"]) if r["fee"].strip() != "" else None)
            for r in csv.DictReader(f)]
sel = [r for r in rows if 10 <= r[0] <= 30]
result = pd.Series(np.array([np.nan if r[2] is None else r[2] for r in sel], dtype="float64"),
                   index=pd.Index(np.array([r[0] for r in sel], dtype="float64"), name="weight_kg"))
