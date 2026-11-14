# M_QF2_02 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("clicks.csv", dtype={"click_ref": str})
ts = pd.to_datetime(df["epoch_s"], unit="s")
df["minute_start"] = ts.dt.floor("min").astype("int64") // 10**9
result = df[["click_ref", "minute_start"]]
