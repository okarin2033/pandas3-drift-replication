# M_QF8_09: naive solution using the invited idiom of catalogue row X01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("daily_temps.csv", parse_dates=["date"])
df = df.set_index("date")
result = df["temp_c"].expanding(min_periods=2).sem().head(30)
