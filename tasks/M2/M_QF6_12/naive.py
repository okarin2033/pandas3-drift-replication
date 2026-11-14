# M_QF6_12: naive solution using the invited idiom of catalogue row N06.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("quiz_scores.csv", dtype="Int64")
result = df["quiz_a"].rank(method="min", ascending=False)
