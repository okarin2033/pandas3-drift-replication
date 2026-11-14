# M_QF1_02 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import json
import pandas as pd

df = pd.read_csv("members.csv")
records = []
for mid, name, city, fee in zip(df["member_id"].tolist(), df["full_name"].tolist(), df["home_city"].tolist(), df["fee"].tolist()):
    if not isinstance(city, str) or city.strip() == "-":
        city = None
    records.append({"member_id": int(mid), "full_name": name, "home_city": city, "fee": float(fee)})
result = json.dumps(records, ensure_ascii=False)
