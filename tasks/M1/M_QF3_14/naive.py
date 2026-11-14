# M_QF3_14 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("gauges.csv")
df["reading"].ffill(inplace=True)
df["site"] = df["site"].str.strip().str.lower()
result = df.groupby("site")["reading"].mean().round(3)
