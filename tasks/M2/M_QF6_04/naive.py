# M_QF6_04: naive solution using the invited idiom of catalogue row N06.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("quiz_scores.csv", dtype_backend="numpy_nullable")
result = df["quiz_a"].rank(pct=True)
