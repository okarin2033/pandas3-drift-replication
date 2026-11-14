# M_QF6_02: naive solution using the invited idiom of catalogue row N02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("store_traffic.csv", dtype_backend="numpy_nullable")
rate = df["sales"] / df["visits"]
result = int(rate.isna().sum())
