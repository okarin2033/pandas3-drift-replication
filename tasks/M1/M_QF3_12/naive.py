# M_QF3_12 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import numpy as np
import pandas as pd

df = pd.read_csv("admissions.csv")
ids = np.array(df["admission_id"])
out = pd.DataFrame({"charge": df["charge"].to_numpy()}, index=pd.Index(ids, name="admission_id"))
ids -= ids.min() - 1
out["new_number"] = ids
result = out
