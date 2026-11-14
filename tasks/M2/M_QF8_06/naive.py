# M_QF8_06: naive solution using the invited idiom of catalogue row X02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("panel_scores.csv")
middle = df.groupby("panel")["score"].quantile(0.5, interpolation="nearest")
above = df["score"] > df["panel"].map(middle)
result = above.groupby(df["panel"]).sum()
