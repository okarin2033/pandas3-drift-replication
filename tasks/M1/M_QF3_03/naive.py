# M_QF3_03 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("bookings.csv")
amounts = df["total"]
amounts[amounts < 0] = 0
result = round(df["total"].sum(), 2)
