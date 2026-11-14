# M_QF5_11: naive solution using the invited idiom of catalogue row R04.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("exam_scores.csv", index_col="student")
long = df.stack()
result = (long < 50).groupby(level=1).mean()
