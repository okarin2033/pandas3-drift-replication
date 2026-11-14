# VERIFY supplementary P+ control N01_c (hand-written; pkg:VERIFY 2026-11-11). Same mechanism as mechanisms/confirm/N01_b.py
# (replace no longer downcasts, so the coded column is dropped by mean(numeric_only=True)), but cause and effect are on ONE line, so the
# first divergent line carries both idioms. Data: mechanisms/confirm/data/N01 (read-only).
import pandas as pd
df = pd.read_csv("orders.csv")
result = df.assign(shipped=df.status.replace({"shipped": 1, "pending": 0})).groupby("city").mean(numeric_only=True)
