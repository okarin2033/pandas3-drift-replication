# M_QF7_07: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("code_changes.csv", encoding="utf-8", newline="") as f:
    rows = [(r["product"], int(r["stock_qty"]), int(r["old_code"]), int(r["new_code"])) for r in csv.DictReader(f)]
result = pd.DataFrame({"product": [r[0] for r in rows], "changed": np.array([r[2] != r[3] for r in rows], dtype="bool")})
