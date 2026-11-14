# M_QF1_03 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
city = df["home_city"].astype(str).str.strip().str.title()
city = city[city != "-"]
result = city.value_counts().sort_index()
