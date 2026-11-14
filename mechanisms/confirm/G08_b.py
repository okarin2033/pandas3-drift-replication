# MECH_B confirmation program G08 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: groupby.any on NaT (b: also median with NaT)
# Why a second attempt: attempt a (large-int sum) gave DTYPE_ONLY
import pandas as pd
df = pd.read_csv("events.csv")
df["when"] = pd.to_datetime(df["when"])
g = df.groupby("k")["when"]
result = pd.DataFrame({"any_date": g.any(), "median_date": g.median()})
