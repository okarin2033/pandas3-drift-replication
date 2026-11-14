# M_QF3_04 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
df = df.fillna(0, inplace=True)
result = df
