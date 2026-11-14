# M_QF4_05 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import numpy as np
import pandas as pd

df = pd.read_csv("subscribers.csv")
df["tier"] = df["tier"].str.strip().str.lower()
result = df.groupby("tier")["monthly_fee"].agg(["mean", np.std]).round(3)
