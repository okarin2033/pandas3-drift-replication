# M_QF6_05: naive solution using the invited idiom of catalogue row N01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("deliveries.csv")
df["city"] = df["city"].str.strip().str.title()
df["express"] = df["express"].fillna(False)
result = (~df["express"]).groupby(df["city"]).sum()
