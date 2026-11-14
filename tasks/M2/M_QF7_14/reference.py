# M_QF7_14: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("parcel_rates.csv", encoding="utf-8", newline="") as f:
    rows = [(float(r["weight_kg"]), int(r["zones"]), float(r["fee"]) if r["fee"].strip() != "" else None)
            for r in csv.DictReader(f)]
sel = [r[1] for r in rows if 20 <= r[0] <= 40]
zs = sorted(set(sel))
result = pd.Series(np.array([sel.count(z) for z in zs], dtype="int64"), index=pd.Index(np.array(zs, dtype="int64"), name="zones"))
