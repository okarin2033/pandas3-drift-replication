# M_QF3_10 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("gauges.csv")
vals, last = [], None
for r in df["reading"].tolist():
    if not pd.isna(r):
        last = float(r)
    vals.append(last)
result = pd.DataFrame({"gauge": df["gauge"].tolist(), "reading": vals,
                       "level": df["level"].astype("int64").tolist(), "site": df["site"].tolist()})
