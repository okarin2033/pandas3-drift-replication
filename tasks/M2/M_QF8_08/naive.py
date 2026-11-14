# M_QF8_08: naive solution using the invited idiom of catalogue row X02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("panel_scores.csv")
middle = df.groupby("panel")["score"].quantile(0.5, interpolation="nearest")
g = df.groupby("panel")["score"]
result = pd.DataFrame({"lowest": g.min(), "middle": middle, "highest": g.max()})
