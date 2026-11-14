# M_QF5_04: naive solution using the invited idiom of catalogue row R05.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

march = pd.read_csv("returns_march.csv")
april = pd.read_csv("returns_april.csv")
both = pd.concat([march, april], ignore_index=True)
result = both["refund"].describe()
