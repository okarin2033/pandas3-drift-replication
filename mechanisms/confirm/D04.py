# MECH_A confirm program D04 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): a daily calendar from date_range, cast to int64.
import pandas as pd

df = pd.read_csv("readings.csv")
days = pd.date_range(df["reading_date"].min(), df["reading_date"].max(), freq="D")
result = pd.Series(days.astype("int64"), name="day_int")
