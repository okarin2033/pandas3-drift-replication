# M_QF1_11 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
names = df["full_name"].str.strip().str.title()
result = int(len(set(names.dropna().tolist())))
