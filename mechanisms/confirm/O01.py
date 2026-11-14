# MECH_A confirm program O01 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): Decimal values written with to_json and read back with json.loads.
import json
from decimal import Decimal
import pandas as pd

df = pd.read_csv("prices.csv", converters={"price": Decimal})
result = json.loads(df.to_json(orient="records"))
