# M_QF4_15 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("purchases.csv")
first = {}
for row in zip(df["purchase_id"].tolist(), df["subscriber_id"].tolist(), df["store_city"].tolist(),
               df["quantity"].tolist(), df["spend"].tolist()):
    sid = int(row[1])
    if sid not in first or int(row[0]) < first[sid][0]:
        first[sid] = (int(row[0]), sid, row[2], int(row[3]), float(row[4]))
keys = sorted(first)
result = pd.DataFrame({"purchase_id": [first[k][0] for k in keys], "subscriber_id": keys,
                       "store_city": [first[k][2] for k in keys], "quantity": [first[k][3] for k in keys],
                       "spend": [first[k][4] for k in keys]})
for c in ("purchase_id", "subscriber_id", "quantity"):
    result[c] = result[c].astype("int64")
