# M_QF1_07 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
labels = []
for v in df["home_city"].tolist():
    if not isinstance(v, str) or v.strip() == "-":
        labels.append("Unknown")
    else:
        labels.append(v.strip().title())
counts = {}
for lab in labels:
    counts[lab] = counts.get(lab, 0) + 1
keys = sorted(counts)
result = pd.Series([counts[k] for k in keys], index=pd.Index(keys), dtype="int64")
