# M_QF1_08 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
city = df["home_city"].astype(str).str.strip().str.title()
city = city.where(city != "-")
codes = city.astype("category").cat.codes
result = pd.DataFrame({"member_id": df["member_id"], "city_code": codes})
