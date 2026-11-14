# M_QF4_09 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
df["tier"] = df["tier"].str.strip().str.lower()
top = df.groupby("tier").apply(
    lambda g: g.sort_values(["monthly_fee", "subscriber_id"], ascending=[False, True]).head(1))
result = top.reset_index(drop=True)
