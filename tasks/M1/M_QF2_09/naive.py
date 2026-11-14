# M_QF2_09 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("quarterly_revenue.csv")
result = pd.infer_freq(pd.to_datetime(df["quarter_start"]))
