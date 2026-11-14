# M_QF5_03: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

SUBJECTS = ["math", "art", "music"]
with open("exam_scores.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
cells = [(r["student"], s, float(r[s])) for r in rows for s in SUBJECTS if r[s].strip() != ""]
result = pd.DataFrame({"student": [c[0] for c in cells], "subject": [c[1] for c in cells],
                       "score": np.array([c[2] for c in cells], dtype="float64")})
