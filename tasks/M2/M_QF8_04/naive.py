# M_QF8_04: naive solution using the invited idiom of catalogue row X02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("panel_scores.csv")
q = df.groupby("panel")["score"].quantile([0.25, 0.5, 0.75], interpolation="nearest").unstack()
q.columns = ["q1", "middle", "q3"]
result = q
