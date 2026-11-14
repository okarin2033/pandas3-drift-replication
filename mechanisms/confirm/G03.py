# MECH_B confirmation program G03 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.groupby(customer_id).apply(lambda g: g.sum(numeric_only=True))
import pandas as pd
df = pd.read_csv("orders.csv")
result = df.groupby("customer_id").apply(lambda g: g.sum(numeric_only=True))
