# M_QF8_07: naive solution using the invited idiom of catalogue row X01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("daily_temps.csv", parse_dates=["date"])
df = df.set_index("date")
se = df["temp_c"].rolling(7).sem()
result = int((se > 0.8).sum())
