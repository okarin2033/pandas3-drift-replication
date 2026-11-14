# M_QF6_14: naive solution using the invited idiom of catalogue row N02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("store_traffic.csv", dtype_backend="numpy_nullable")
df["rate"] = df["sales"] / df["visits"]
result = df.sort_values("rate", ascending=False).head(3)[["store", "rate"]].reset_index(drop=True)
