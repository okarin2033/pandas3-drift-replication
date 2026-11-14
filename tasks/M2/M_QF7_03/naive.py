# M_QF7_03: naive solution using the invited idiom of catalogue row I05.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("code_changes.csv")
lookup = df.set_index("old_code")
df["unchanged"] = lookup.index == lookup["new_code"]
result = df
