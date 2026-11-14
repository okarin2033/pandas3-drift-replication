# M_QF4_10 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
cnt = {}
for t in df["tier"].tolist():
    k = t.strip().lower()
    cnt[k] = cnt.get(k, 0) + 1
keys = sorted(cnt)
result = pd.DataFrame({"tier": keys, "subscribers": [cnt[k] for k in keys]})
result["subscribers"] = result["subscribers"].astype("int64")
