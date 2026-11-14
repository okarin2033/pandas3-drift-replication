# M_QF5_14: naive solution using the invited idiom of catalogue row R02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("memberships.csv", dtype={"member_ref": str})
df["city"] = df["city"].str.strip().str.title()
result = df[["plan", "city"]].value_counts(sort=False).head(6)
