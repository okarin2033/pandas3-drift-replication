# M_QF1_05 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import json
import pandas as pd

df = pd.read_csv("price_list.csv", dtype={"price": str})
records = [{"sku": s, "item": i, "section": sec, "price": float(p)}
           for s, i, sec, p in zip(df["sku"].tolist(), df["item"].tolist(), df["section"].tolist(), df["price"].tolist())]
result = pd.DataFrame(json.loads(json.dumps(records)), columns=["sku", "item", "section", "price"])
