# MECH_B confirmation program G01 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.groupby(pd.cut(df.age, bins, labels=labels)).monthly_spend.agg([count, mean]) (empty bins dropped)
import pandas as pd
df = pd.read_csv("customers.csv")
bins = [0, 18, 30, 45, 60, 100]
labels = ["under_18", "18_29", "30_44", "45_59", "60_plus"]
result = df.groupby(pd.cut(df.age, bins, labels=labels)).monthly_spend.agg(["count", "mean"])
