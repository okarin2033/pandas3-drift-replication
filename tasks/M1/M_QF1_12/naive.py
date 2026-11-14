# M_QF1_12 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
df["home_city"] = df["home_city"].str.strip().replace("-", None)
df = df.where(df.notna(), None)
result = sorted(int(m) for m, c in zip(df["member_id"], df["home_city"]) if c is None)
