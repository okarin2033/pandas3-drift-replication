# M_QF6_15: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("quiz_scores.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
QUIZZES = ["quiz_a", "quiz_b"]
score = {q: [int(r[q]) if r[q].strip() != "" else None for r in rows] for q in QUIZZES}
marks = {"quiz_a": 6, "quiz_b": 5}
result = int(sum(1 for i in range(len(rows))
                 if any(score[q][i] is not None and score[q][i] < marks[q] for q in QUIZZES)))
