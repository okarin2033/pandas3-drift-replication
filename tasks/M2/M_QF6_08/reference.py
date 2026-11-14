# M_QF6_08: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("quiz_scores.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
QUIZZES = ["quiz_a", "quiz_b"]
score = {q: [int(r[q]) if r[q].strip() != "" else None for r in rows] for q in QUIZZES}


def avg_ranks(vals, ascending=True):
    """Average ranks (1 = first in sort order) of the non-missing values; None for missing."""
    present = sorted((v for v in vals if v is not None), reverse=not ascending)
    first = {}
    for i, v in enumerate(present, 1):
        first.setdefault(v, []).append(i)
    return [None if v is None else sum(first[v]) / len(first[v]) for v in vals]


def min_ranks(vals, ascending=True):
    present = sorted((v for v in vals if v is not None), reverse=not ascending)
    first = {}
    for i, v in enumerate(present, 1):
        first.setdefault(v, i)
    return [None if v is None else float(first[v]) for v in vals]
r = avg_ranks(score["quiz_b"])
result = pd.Series(np.array([np.nan if x is None else x for x in r], dtype="float64"))
