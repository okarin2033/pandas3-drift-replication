# MECH_A confirm program D01 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): parsed dates cast to int64 and divided by 10**9 as Unix seconds.
import pandas as pd

df = pd.read_csv("users.csv")
df["signup_date"] = pd.to_datetime(df["signup_date"])
df["signup_unix"] = df["signup_date"].astype("int64") // 10**9
result = df[["user_id", "signup_unix"]]
