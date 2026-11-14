# M_QF2_03 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("shipments.csv")
month_end = pd.to_datetime(df["ordered_on"]).dt.to_period("M").dt.end_time
result = df.groupby(month_end)["value"].sum()
