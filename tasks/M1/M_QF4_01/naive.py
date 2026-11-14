# M_QF4_01 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
labels = ["under 18", "18-29", "30-44", "45-59", "60+"]
band = pd.cut(df["age"], [0, 18, 30, 45, 60, float("inf")], right=False, labels=labels)
result = df.groupby(band).agg(subscribers=("subscriber_id", "count"), mean_fee=("monthly_fee", "mean")).round(2)
