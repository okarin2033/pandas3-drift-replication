# M_QF1_12 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
ids = []
for mid, city in zip(df["member_id"].tolist(), df["home_city"].tolist()):
    if not isinstance(city, str) or city.strip() == "-":
        ids.append(int(mid))
result = sorted(ids)
