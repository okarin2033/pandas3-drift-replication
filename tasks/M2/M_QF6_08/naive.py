# M_QF6_08: naive solution using the invited idiom of catalogue row N06.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("quiz_scores.csv").convert_dtypes()
result = df["quiz_b"].rank()
