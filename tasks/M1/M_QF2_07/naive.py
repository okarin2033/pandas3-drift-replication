# M_QF2_07 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("clicks.csv", dtype=str)
ts = pd.to_datetime(df["epoch_s"], unit="s", errors="coerce")
result = ts.dt.strftime("%Y-%m-%d").value_counts().sort_index()
