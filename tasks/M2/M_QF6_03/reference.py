# M_QF6_03: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("quiz_scores.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
QUIZZES = ["quiz_a", "quiz_b"]
score = {q: [int(r[q]) if r[q].strip() != "" else None for r in rows] for q in QUIZZES}
marks = {"quiz_a": 6, "quiz_b": 5}
shares = [sum(1 for v in score[q] if v is not None and v >= marks[q]) / len(rows) for q in QUIZZES]
result = pd.Series(np.array(shares, dtype="float64"), index=QUIZZES)
