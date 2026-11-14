# F-main re-check program for catalogue row D10 (FIX, STAGE2 T3.4). Written 2026-11-11 by pkg:FIX.
# Copy of mechanisms/confirm/D10.py (deciding attempt; original unchanged) with ONLY file and column names
# replaced: logins.csv -> sessions.csv, login_time -> started_at
# Header comments of the original dropped; code lines otherwise identical (diff in logs/fix/fmain_diffs_2026-11-11.txt).
import pandas as pd

df = pd.read_csv("sessions.csv")
df["started_at"] = pd.to_datetime(df["started_at"])
df = df.sort_values("started_at")
result = df["started_at"].dt.to_pydatetime()[0]
