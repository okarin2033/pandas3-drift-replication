# M_QF4_07 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
bands = [("under 5", 0, 5), ("5-10", 5, 10), ("10-20", 10, 20), ("20-30", 20, 30), ("30+", 30, float("inf"))]
fees = [float(f) for f in df["monthly_fee"].tolist() if not pd.isna(f)]
counts = [sum(1 for f in fees if lo <= f < hi) for _, lo, hi in bands]
result = pd.Series(counts, index=pd.Index([b[0] for b in bands]), dtype="int64")
