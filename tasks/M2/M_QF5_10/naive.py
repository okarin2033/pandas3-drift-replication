# M_QF5_10: naive solution using the invited idiom of catalogue row R02.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("memberships.csv", dtype={"member_ref": str})
counts = df.groupby("plan")["points"].value_counts(sort=False)
result = counts.groupby(level="plan").head(3)
