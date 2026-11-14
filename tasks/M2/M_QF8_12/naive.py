# M_QF8_12: naive solution using the invited idiom of catalogue row X02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("panel_scores.csv")
middle = df.groupby("panel")["score"].quantile(0.5, interpolation="nearest")
df["entrant"] = df["entrant"].str.strip()
hits = df[df["score"] == df["panel"].map(middle)]
result = hits[["panel", "entrant", "score"]].reset_index(drop=True)
