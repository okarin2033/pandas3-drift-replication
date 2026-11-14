# M_QF7_14: naive solution using the invited idiom of catalogue row I02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("parcel_rates.csv")
table = df.set_index("weight_kg")
result = table[20:40]["zones"].value_counts().sort_index()
