# M_QF3_15 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("gauges.csv")
lv = df["level"]
lv[lv > 50] = 50
df["site"] = df["site"].str.strip().str.lower()
result = df[["gauge", "site", "level"]]
