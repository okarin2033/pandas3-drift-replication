# M_QF1_06 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("price_list.csv")
section = df["section"].str.strip().str.lower()
d = pd.DataFrame({"section": section.tolist(), "price": df["price"].tolist()})
result = d.groupby("section")["price"].mean().round(2).sort_index()
