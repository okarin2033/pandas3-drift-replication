# M_QF6_13: naive solution using the invited idiom of catalogue row N01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("deliveries.csv")
df["city"] = df["city"].str.strip().str.title()
df["express"] = df["express"].ffill()
result = df[["city", "express", "parcels"]].groupby("city").mean(numeric_only=True)
