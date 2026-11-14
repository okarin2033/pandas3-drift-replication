# M_QF6_06: naive solution using the invited idiom of catalogue row N02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("store_traffic.csv").convert_dtypes()
df["rate"] = df["sales"] / df["visits"]
result = df.groupby("store")["rate"].mean()
