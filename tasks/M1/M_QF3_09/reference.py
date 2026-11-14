# M_QF3_09 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
mx, n85 = {}, {}
for w, a in zip(df["ward"].tolist(), df["age"].tolist()):
    k = w.strip().lower()
    mx.setdefault(k, None)
    n85.setdefault(k, 0)
    if pd.isna(a):
        continue
    a = min(float(a), 85.0)
    mx[k] = a if mx[k] is None else max(mx[k], a)
    n85[k] += int(a == 85.0)
keys = sorted(mx)
result = pd.DataFrame({"max_age": [mx[k] for k in keys], "patients_at_85": [n85[k] for k in keys]},
                      index=pd.Index(keys))
result["patients_at_85"] = result["patients_at_85"].astype("int64")
