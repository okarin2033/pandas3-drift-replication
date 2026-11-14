# M_QF5_15: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

SUBJECTS = ["math", "art", "music"]
with open("exam_scores.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
cells = [(r["student"], s, float(r[s])) for r in rows for s in SUBJECTS if r[s].strip() != ""]
result = float(sum(1 for c in cells if c[2] >= 90) / len(cells))
