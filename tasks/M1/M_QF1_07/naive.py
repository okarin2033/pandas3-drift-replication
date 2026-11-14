# M_QF1_07 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
city = df["home_city"].str.strip()
city = city.where(city != "-", None)
city = city.where(city.notna(), None)
city = city.map(lambda v: "Unknown" if v is None else v).str.title()
result = city.value_counts().sort_index()
