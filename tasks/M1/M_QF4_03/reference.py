# M_QF4_03 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("purchases.csv")
q, s = {}, {}
for sid, qty, sp in zip(df["subscriber_id"].tolist(), df["quantity"].tolist(), df["spend"].tolist()):
    q[int(sid)] = q.get(int(sid), 0) + int(qty)
    s[int(sid)] = s.get(int(sid), 0.0) + float(sp)
keys = sorted(q)
result = pd.DataFrame({"quantity": [q[k] for k in keys], "spend": [round(s[k], 2) for k in keys]},
                      index=pd.Index(keys, dtype="int64"))
result["quantity"] = result["quantity"].astype("int64")
