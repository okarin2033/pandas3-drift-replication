# M_QF2_04 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("signups.csv")
df["signup_day"] = pd.to_datetime(df["signup_day"])
days = pd.date_range(df["signup_day"].min(), df["signup_day"].max(), freq="D")
counts = df["signup_day"].value_counts().reindex(days, fill_value=0)
counts.index = days.astype("int64") // 10**9
result = counts
