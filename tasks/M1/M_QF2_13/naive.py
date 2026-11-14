# M_QF2_13 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("quarterly_revenue.csv")
df["quarter_end"] = pd.to_datetime(df["quarter_start"]).dt.to_period("Q").dt.end_time
result = df[["quarter_end", "revenue"]].sort_values("quarter_end").reset_index(drop=True)
