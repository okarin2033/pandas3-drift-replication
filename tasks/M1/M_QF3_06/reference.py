# M_QF3_06 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("gauges.csv")
lv = [int(v) for v in df["level"].tolist()]
lo = min(lv)
result = pd.DataFrame({"reading": df["reading"].tolist(), "level_above_min": [v - lo for v in lv]},
                      index=pd.Index(lv, dtype="int64"))
result["level_above_min"] = result["level_above_min"].astype("int64")
