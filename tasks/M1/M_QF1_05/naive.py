# M_QF1_05 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import json
from decimal import Decimal
import pandas as pd

df = pd.read_csv("price_list.csv", converters={"price": Decimal})
result = pd.DataFrame(json.loads(df.to_json(orient="records")))
