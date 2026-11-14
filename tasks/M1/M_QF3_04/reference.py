# M_QF3_04 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("admissions.csv")
def z(v):
    return 0.0 if pd.isna(v) else float(v)
result = pd.DataFrame({
    "admission_id": df["admission_id"].astype("int64").tolist(),
    "age": [z(v) for v in df["age"].tolist()],
    "ward": df["ward"].tolist(),
    "stay_days": [z(v) for v in df["stay_days"].tolist()],
    "charge": [z(v) for v in df["charge"].tolist()],
})
