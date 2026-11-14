# M_QF2_12 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("clicks.csv")
ts = pd.to_datetime(df["epoch_ms"], unit="ms")
result = pd.to_datetime(ts.astype("int64").median())
