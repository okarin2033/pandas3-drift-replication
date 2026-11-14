# MECH_A confirm program D10 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): Series.dt.to_pydatetime()[0] after sorting (earliest login).
import pandas as pd

df = pd.read_csv("logins.csv")
df["login_time"] = pd.to_datetime(df["login_time"])
df = df.sort_values("login_time")
result = df["login_time"].dt.to_pydatetime()[0]
