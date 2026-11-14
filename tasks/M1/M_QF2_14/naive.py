# M_QF2_14 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("shipments.csv")
d = pd.to_datetime(df["ordered_on"])
all_days = pd.date_range(d.min(), d.max(), freq="D")
missing = all_days.difference(pd.DatetimeIndex(d.unique()))
result = sorted((missing.astype("int64") // (86400 * 10**9)).tolist())
