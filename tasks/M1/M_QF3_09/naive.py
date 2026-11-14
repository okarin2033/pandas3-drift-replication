# M_QF3_09 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
ages = df["age"]
ages[ages > 85] = 85
df["ward"] = df["ward"].str.strip().str.lower()
result = df.groupby("ward").agg(max_age=("age", "max"), patients_at_85=("age", lambda s: int((s == 85).sum())))
