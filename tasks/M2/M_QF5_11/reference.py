# M_QF5_11: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

SUBJECTS = ["math", "art", "music"]
with open("exam_scores.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
cells = [(r["student"], s, float(r[s])) for r in rows for s in SUBJECTS if r[s].strip() != ""]
shares = []
for s in ["math", "art", "music"]:
    vals = [c[2] for c in cells if c[1] == s]
    shares.append(sum(1 for v in vals if v < 50) / len(vals))
result = pd.Series(np.array(shares, dtype="float64"), index=pd.Index(["math", "art", "music"], name="subject"))
