# M_QF4_12 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("purchases.csv")
df = df.dropna(subset=["store_city"])
df["store_city"] = df["store_city"].str.strip().str.title()
df = df.set_index("store_city")
lines = []
for city, grp in df.groupby(level=["store_city"]):
    lines.append(f"{city}: {len(grp)} purchases")
result = lines
