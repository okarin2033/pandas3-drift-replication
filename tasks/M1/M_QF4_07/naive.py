# M_QF4_07 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
labels = ["under 5", "5-10", "10-20", "20-30", "30+"]
band = pd.cut(df["monthly_fee"], [0, 5, 10, 20, 30, float("inf")], right=False, labels=labels)
result = df.groupby(band).size()
