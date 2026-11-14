# M_QF3_02 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import statistics
import pandas as pd

df = pd.read_csv("admissions.csv")
known = [float(a) for a in df["age"].tolist() if not pd.isna(a)]
med = statistics.median(known)
acc = {}
for w, a in zip(df["ward"].tolist(), df["age"].tolist()):
    acc.setdefault(w.strip().lower(), []).append(med if pd.isna(a) else float(a))
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 1) for k in keys], index=pd.Index(keys))
