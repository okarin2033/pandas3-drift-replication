# M_QF3_16 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("bookings.csv")
states = []
for s in df["state"].tolist():
    s = s.strip().lower()
    states.append("open" if s == "pending" else s)
result = pd.DataFrame({"booking_id": df["booking_id"].astype("int64").tolist(), "state": states,
                       "total": df["total"].tolist(), "nights": df["nights"].tolist()})
