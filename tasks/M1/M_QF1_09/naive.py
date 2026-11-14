# M_QF1_09 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv", dtype={"fee": "category"})
result = df["fee"].value_counts().sort_index()
