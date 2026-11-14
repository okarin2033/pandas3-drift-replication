# M_QF7_16: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("storage_quota.csv", encoding="utf-8", newline="") as f:
    rows = [(int(r["account_id"]), r["active"] == "True", int(r["quota_bytes"]), int(r["used_bytes"]))
            for r in csv.DictReader(f)]
# exact Python integers: active counts 1 or 0
control = [(a, int(act) + q + u) for a, act, q, u in rows]
keys = [False, True]
sums = [sum(c for (a, act, q, u), (_, c) in zip(rows, control) if act == k) for k in keys]
result = pd.Series(sums, index=pd.Index(np.array(keys, dtype="bool"), name="active"), dtype="object")
