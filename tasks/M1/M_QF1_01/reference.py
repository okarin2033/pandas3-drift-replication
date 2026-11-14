# M_QF1_01 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
city = df["home_city"].str.strip().str.title()
keep = city.notna() & (city != "-")
d = pd.DataFrame({"home_city": city[keep].tolist(), "fee": df.loc[keep, "fee"].tolist()})
g = d.groupby("home_city")["fee"]
out = pd.DataFrame({"members": g.size(), "total_fee": g.sum().round(2)})
out = out.sort_index().reset_index()
out["members"] = out["members"].astype("int64")
result = out
