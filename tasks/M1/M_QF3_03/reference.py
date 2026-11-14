# M_QF3_03 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import math
import pandas as pd

df = pd.read_csv("bookings.csv")
result = round(math.fsum(max(float(t), 0.0) for t in df["total"].tolist()), 2)
