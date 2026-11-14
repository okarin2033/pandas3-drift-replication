# M_QF7_06: naive solution using the invited idiom of catalogue row I02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("parcel_rates.csv")
fees = df.set_index("weight_kg")["fee"]
result = float(fees[5:15].mean())
