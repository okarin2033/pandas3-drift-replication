# M_QF3_02 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
df["age"].fillna(df["age"].median(), inplace=True)
df["ward"] = df["ward"].str.strip().str.lower()
result = df.groupby("ward")["age"].mean().round(1)
