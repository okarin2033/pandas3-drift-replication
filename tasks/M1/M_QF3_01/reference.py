# M_QF3_01 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("bookings.csv")
tot = {}
for st, t in zip(df["state"].tolist(), df["total"].tolist()):
    k = st.strip().lower()
    tot[k] = tot.get(k, 0.0) + (0.0 if k == "cancelled" else float(t))
keys = sorted(tot)
result = pd.Series([round(tot[k], 2) for k in keys], index=pd.Index(keys))
