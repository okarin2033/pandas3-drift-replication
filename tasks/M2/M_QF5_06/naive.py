# M_QF5_06: naive solution using the invited idiom of catalogue row R02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("memberships.csv", dtype={"member_ref": str})
result = df[["plan", "points"]].value_counts(sort=False).head(5)
