# VERIFY harm-prelabel wiring check: a reference that neither version matches (days since 1970 instead of seconds) -> NEITHER.
import pandas as pd
df = pd.read_csv("users.csv")
df["signup_date"] = pd.to_datetime(df["signup_date"])
df["signup_days"] = (df["signup_date"] - pd.Timestamp("1970-01-01")).dt.days
result = df[["user_id", "signup_days"]]
