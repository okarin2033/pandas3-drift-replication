# M_QF4_13 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("purchases.csv")
labels = ["small", "medium", "large", "very large"]
cls = pd.cut(df["spend"], [0, 25, 100, 250, float("inf")], right=False, labels=labels)
result = df.groupby(cls).agg(purchases=("purchase_id", "count"), total_spend=("spend", "sum")).round(2)
