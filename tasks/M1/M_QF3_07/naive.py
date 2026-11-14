# M_QF3_07 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
df["stay_days"][df["stay_days"] > 14] = 14
df["ward"] = df["ward"].str.strip().str.lower()
result = df.groupby("ward")["stay_days"].mean().round(2)
