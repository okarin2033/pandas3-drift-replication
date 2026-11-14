# F-main re-check program for catalogue row D01 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/D01.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: users.csv -> signups.csv, signup_date -> signup_day, user_id -> account_id
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("signups.csv")
df["signup_day"] = pd.to_datetime(df["signup_day"])
df["signup_unix"] = df["signup_day"].astype("int64") // 10**9
result = df[["account_id", "signup_unix"]]
