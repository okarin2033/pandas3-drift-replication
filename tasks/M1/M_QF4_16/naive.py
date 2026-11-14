# M_QF4_16 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
period = (df["joined_year"] // 5 * 5).rename("period_start")
out = df.groupby(period, as_index=False)["monthly_fee"].mean().round(2)
result = out.rename(columns={"monthly_fee": "mean_fee"})
