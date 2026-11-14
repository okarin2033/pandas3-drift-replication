# M_QF3_01 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("bookings.csv")
df["state"] = df["state"].str.strip().str.lower()
df["total"][df["state"] == "cancelled"] = 0
result = df.groupby("state")["total"].sum()
