# M_QF8_05: naive solution using the invited idiom of catalogue row X01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("daily_temps.csv", parse_dates=["date"])
df = df.set_index("date")
result = df["humidity"].rolling(10).sem()
