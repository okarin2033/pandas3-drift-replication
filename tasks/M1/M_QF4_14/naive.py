# M_QF4_14 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("unit_sales.csv")
df["region"] = pd.Categorical(df["region"], categories=["north", "south", "west"])
df["channel"] = pd.Categorical(df["channel"], categories=["online", "store", "kiosk"])
counts = df.groupby(["region", "channel"], observed=False).apply(lambda g: int(g["units"].isna().sum()))
result = counts.reset_index(name="missing_weeks")
