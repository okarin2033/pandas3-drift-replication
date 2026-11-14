# M_QF6_15: naive solution using the invited idiom of catalogue row N05.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("quiz_scores.csv")
marks = pd.Series({"quiz_a": 6, "quiz_b": 5}, dtype="Int64")
passed = df >= marks
result = int((~passed).any(axis=1).sum())
