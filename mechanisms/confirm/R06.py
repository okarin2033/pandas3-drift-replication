# MECH_B confirmation program R06 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: pd.qcut(df.amount, 4) bin edge values (attempt a)
import pandas as pd
df = pd.read_csv("orders.csv")
result = df.assign(quartile=pd.qcut(df.amount, 4, labels=["q1", "q2", "q3", "q4"]))
