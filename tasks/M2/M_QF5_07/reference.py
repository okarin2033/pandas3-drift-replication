# M_QF5_07: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

SUBJECTS = ["math", "art", "music"]
with open("exam_scores.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
cells = [(r["student"], s, float(r[s])) for r in rows for s in SUBJECTS if r[s].strip() != ""]
order, counts = [], {}
for student, _, _ in cells:
    if student not in counts:
        order.append(student)
        counts[student] = 0
    counts[student] += 1
result = pd.Series(np.array([counts[s] for s in order], dtype="int64"), index=pd.Index(order, name="student"))
