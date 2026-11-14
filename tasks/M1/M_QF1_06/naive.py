# M_QF1_06 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("price_list.csv")
for c in df.columns:
    if df[c].dtype == "O":
        df[c] = df[c].str.strip().str.lower()
result = df.groupby("section")["price"].mean().round(2)
