# M_QF8_03: naive solution using the invited idiom of catalogue row X01.
# drafted_by pkg:TASKS_M2 (2026-11-11); status: prepared.
import pandas as pd

df = pd.read_csv("daily_temps.csv", parse_dates=["date"])
df = df.set_index("date")
roll = df["temp_c"].rolling(7)
mean = roll.mean()
se = roll.sem()
result = pd.DataFrame({"mean": mean, "lower": mean - 1.96 * se, "upper": mean + 1.96 * se})
