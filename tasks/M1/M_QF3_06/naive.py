# M_QF3_06 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import numpy as np
import pandas as pd

df = pd.read_csv("gauges.csv")
levels = np.array(df["level"], dtype="int64")
out = pd.DataFrame({"reading": df["reading"].to_numpy()}, index=pd.Index(levels, name="level"))
levels -= levels.min()
out["level_above_min"] = levels
result = out
