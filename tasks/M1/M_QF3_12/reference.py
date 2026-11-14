# M_QF3_12 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
ids = [int(v) for v in df["admission_id"].tolist()]
result = pd.DataFrame({"charge": df["charge"].tolist(), "new_number": list(range(1, len(ids) + 1))},
                      index=pd.Index(ids, dtype="int64"))
result["new_number"] = result["new_number"].astype("int64")
