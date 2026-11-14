# MECH_B confirmation program N04 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df.col.value_counts().index.dtype ; sorted index operations (b: object column of timestamps)
# Why a second attempt: attempt a (object column of ints) gave IDENTICAL (index object on 2.3.3 too)
import pandas as pd
df = pd.read_csv("days.csv")
days = pd.to_datetime(df["day"]).astype(object)
vc = days.value_counts()
result = vc.reset_index().describe()
