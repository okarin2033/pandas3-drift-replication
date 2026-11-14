# M_QF4_01 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
bands = [("under 18", 0, 18), ("18-29", 18, 30), ("30-44", 30, 45), ("45-59", 45, 60), ("60+", 60, float("inf"))]
rows = []
for lab, lo, hi in bands:
    n, fees = 0, []
    for a, f in zip(df["age"].tolist(), df["monthly_fee"].tolist()):
        if not pd.isna(a) and lo <= a < hi:
            n += 1
            if not pd.isna(f):
                fees.append(float(f))
    rows.append((lab, n, round(sum(fees) / len(fees), 2) if fees else float("nan")))
result = pd.DataFrame({"subscribers": [r[1] for r in rows], "mean_fee": [r[2] for r in rows]},
                      index=pd.Index([r[0] for r in rows]))
result["subscribers"] = result["subscribers"].astype("int64")
