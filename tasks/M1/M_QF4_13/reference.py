# M_QF4_13 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import math
import pandas as pd

df = pd.read_csv("purchases.csv")
classes = [("small", 0, 25), ("medium", 25, 100), ("large", 100, 250), ("very large", 250, float("inf"))]
sp = [float(s) for s in df["spend"].tolist()]
rows = [(lab, sum(1 for s in sp if lo <= s < hi), round(math.fsum(s for s in sp if lo <= s < hi), 2)) for lab, lo, hi in classes]
result = pd.DataFrame({"purchases": [r[1] for r in rows], "total_spend": [r[2] for r in rows]},
                      index=pd.Index([r[0] for r in rows]))
result["purchases"] = result["purchases"].astype("int64")
