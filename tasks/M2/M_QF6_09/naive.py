# M_QF6_09: naive solution using the invited idiom of catalogue row N01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("deliveries.csv")
df["shipped"] = df["status"].replace({"shipped": 1, "pending": 0})
result = df[["shipped", "parcels"]].corr(numeric_only=True)
