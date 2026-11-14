# M_QF2_01 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("signups.csv")
df = df.dropna(subset=["channel"])
df["channel"] = df["channel"].str.strip().str.lower()
df["signup_day"] = pd.to_datetime(df["signup_day"])
df["unix_s"] = df["signup_day"].astype("int64") // 10**9
result = df.groupby("channel")["unix_s"].agg(first_signup="min", last_signup="max")
