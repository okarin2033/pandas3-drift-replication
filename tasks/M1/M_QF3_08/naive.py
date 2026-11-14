# M_QF3_08 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
df["charge"].fillna(0, inplace=True)
df["ward"] = df["ward"].str.strip().str.lower()
result = df.groupby("ward")["charge"].mean().round(2)
