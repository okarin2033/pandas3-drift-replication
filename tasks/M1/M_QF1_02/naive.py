# M_QF1_02 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import json
import pandas as pd

df = pd.read_csv("members.csv")
df.loc[df["home_city"].str.strip() == "-", "home_city"] = None
df = df.where(pd.notnull(df), None)
result = json.dumps(df.to_dict(orient="records"), ensure_ascii=False)
