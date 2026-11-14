# M_QF1_15 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import json
import pandas as pd

df = pd.read_csv("price_list.csv", dtype={"price": str})
result = json.loads(json.dumps({s: p for s, p in zip(df["sku"].tolist(), df["price"].tolist())}))
