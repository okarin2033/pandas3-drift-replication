# M_QF2_02 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("clicks.csv", dtype={"click_ref": str})
mins = [int(s) // 60 * 60 for s in df["epoch_s"].tolist()]
result = pd.DataFrame({"click_ref": df["click_ref"].tolist(), "minute_start": mins})
result["minute_start"] = result["minute_start"].astype("int64")
