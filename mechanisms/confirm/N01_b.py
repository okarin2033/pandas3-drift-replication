# MECH_B confirmation program N01 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: s = df.status.replace({shipped: 1, pending: 0}) (b: the coded column then used in a numeric summary)
# Why a second attempt: attempt a (sorted codes) gave DTYPE_ONLY
import pandas as pd
df = pd.read_csv("orders.csv")
df["shipped"] = df.status.replace({"shipped": 1, "pending": 0})
result = df.groupby("city").mean(numeric_only=True)
