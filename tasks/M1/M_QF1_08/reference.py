# M_QF1_08 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
tidy = []
for v in df["home_city"].tolist():
    tidy.append(v.strip().title() if isinstance(v, str) and v.strip() != "-" else None)
order = sorted({t for t in tidy if t is not None})
code_of = {c: i for i, c in enumerate(order)}
codes = [code_of[t] if t is not None else -1 for t in tidy]
result = pd.DataFrame({"member_id": df["member_id"].astype("int64").tolist(), "city_code": codes})
result["city_code"] = result["city_code"].astype("int64")
