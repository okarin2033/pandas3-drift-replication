# M_QF7_06: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("parcel_rates.csv", encoding="utf-8", newline="") as f:
    rows = [(float(r["weight_kg"]), int(r["zones"]), float(r["fee"]) if r["fee"].strip() != "" else None)
            for r in csv.DictReader(f)]
vals = [r[2] for r in rows if 5 <= r[0] <= 15 and r[2] is not None]
result = float(sum(vals) / len(vals))
