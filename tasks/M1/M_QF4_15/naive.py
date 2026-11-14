# M_QF4_15 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("purchases.csv")
result = df.groupby("subscriber_id").apply(lambda g: g.sort_values("purchase_id").iloc[0])
