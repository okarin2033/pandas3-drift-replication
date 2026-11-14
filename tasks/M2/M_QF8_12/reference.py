# M_QF8_12: version-robust reference solution.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import csv
import numpy as np
import pandas as pd

with open("panel_scores.csv", encoding="utf-8", newline="") as f:
    rows = [(r["panel"], r["entrant"], float(r["score"])) for r in csv.DictReader(f)]
panels = sorted({p for p, _, _ in rows})


def middle(scores, tie):
    """The score at the middle position of the sorted scores; with an even count the two middle scores are equally near
    and `tie` ('lower' or 'higher') picks one."""
    s = sorted(scores)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return s[n // 2 - 1] if tie == "lower" else s[n // 2]


def nearest_pos(scores, q):
    """Score at the sorted position nearest to q * (n - 1) (counting from 0); only used where that position is not a tie."""
    s = sorted(scores)
    return s[int(round(q * (len(s) - 1)))]


by_panel = {p: [sc for pp, _, sc in rows if pp == p] for p in panels}
mid = {p: middle(by_panel[p], "lower") for p in panels}
sel = [(p, e.strip(), sc) for p, e, sc in rows if sc == mid[p]]
result = pd.DataFrame({"panel": [s[0] for s in sel], "entrant": [s[1] for s in sel],
                       "score": np.array([s[2] for s in sel], dtype="float64")})
