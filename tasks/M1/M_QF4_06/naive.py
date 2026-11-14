# M_QF4_06 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
df["tier"] = df["tier"].str.strip().str.lower()
df = df.set_index("tier")
totals = {}
for tier, grp in df.groupby(level=["tier"]):
    totals[tier] = round(float(grp["monthly_fee"].sum()), 2)
result = totals
