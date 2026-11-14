# M_QF4_11 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import numpy as np
import pandas as pd

df = pd.read_csv("purchases.csv")
city = df["store_city"].str.strip().str.title()
result = df.groupby(city)["spend"].agg(np.var).round(2)
