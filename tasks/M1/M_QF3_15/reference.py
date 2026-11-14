# M_QF3_15 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("gauges.csv")
result = pd.DataFrame({"gauge": df["gauge"].tolist(),
                       "site": [s.strip().lower() for s in df["site"].tolist()],
                       "level": [min(int(v), 50) for v in df["level"].tolist()]})
result["level"] = result["level"].astype("int64")
