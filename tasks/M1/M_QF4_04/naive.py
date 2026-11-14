# M_QF4_04 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("purchases.csv")
result = df.groupby(df["store_city"].str.strip().str.title(), as_index=False)["spend"].sum()
