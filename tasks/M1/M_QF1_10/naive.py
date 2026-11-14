# M_QF1_10 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import json
from decimal import Decimal
import pandas as pd

df = pd.read_csv("price_list.csv", converters={"price": Decimal})
df["section"] = df["section"].str.strip().str.lower()
totals = df.groupby("section")["price"].sum()
result = json.loads(totals.to_json())
