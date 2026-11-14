# M_QF3_16 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("bookings.csv")
df["state"] = df["state"].str.strip().str.lower()
result = df.replace({"state": {"pending": "open"}}, inplace=True)
