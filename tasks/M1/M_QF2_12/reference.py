# M_QF2_12 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("clicks.csv")
ms = sorted(int(v) for v in df["epoch_ms"].tolist())
n = len(ms)
twice = ms[n // 2] * 2 if n % 2 else ms[n // 2 - 1] + ms[n // 2]
result = pd.Timestamp(twice * 500, unit="us")
