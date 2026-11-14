# M_QF4_09 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
best = {}
for sid, tier, fee in zip(df["subscriber_id"].tolist(), df["tier"].tolist(), df["monthly_fee"].tolist()):
    if pd.isna(fee):
        continue
    k = tier.strip().lower()
    cand = (-float(fee), int(sid))
    if k not in best or cand < best[k]:
        best[k] = cand
keys = sorted(best)
result = pd.DataFrame({"tier": keys, "subscriber_id": [best[k][1] for k in keys],
                       "monthly_fee": [-best[k][0] for k in keys]})
result["subscriber_id"] = result["subscriber_id"].astype("int64")
