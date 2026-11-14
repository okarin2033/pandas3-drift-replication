# M_QF7_04: naive solution using the invited idiom of catalogue row I06.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("storage_quota.csv")
control = df[["active", "quota_bytes", "used_bytes"]].sum(axis=1)
control.index = df["account_id"]
result = control
