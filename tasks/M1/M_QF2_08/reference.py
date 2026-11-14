# M_QF2_08 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("shipments.csv")
base = dt.date(2025, 1, 1)
def days(v):
    return float((dt.date.fromisoformat(v) - base).days) if isinstance(v, str) else float("nan")
out = pd.DataFrame({
    "shipment_id": df["shipment_id"].astype("int64").tolist(),
    "ordered_on": [days(v) for v in df["ordered_on"].tolist()],
    "shipped_on": [days(v) for v in df["shipped_on"].tolist()],
    "carrier": df["carrier"].tolist(),
    "weight_kg": df["weight_kg"].tolist(),
    "value": df["value"].tolist(),
})
result = out
