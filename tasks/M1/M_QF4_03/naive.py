# M_QF4_03 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("purchases.csv")
result = df.drop(columns="purchase_id").groupby("subscriber_id").apply(lambda g: g.sum(numeric_only=True))
