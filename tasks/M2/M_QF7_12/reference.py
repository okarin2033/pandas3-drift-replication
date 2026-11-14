# M_QF7_12: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("storage_quota.csv", encoding="utf-8", newline="") as f:
    rows = [(int(r["account_id"]), r["active"] == "True", int(r["quota_bytes"]), int(r["used_bytes"]))
            for r in csv.DictReader(f)]
# exact Python integers: active counts 1 or 0
control = [(a, int(act) + q + u) for a, act, q, u in rows]
result = int(sum(c for _, c in control))
