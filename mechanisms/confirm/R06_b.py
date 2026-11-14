# MECH_B confirmation program R06 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: pd.pivot_table(df, values=amount, index=category, columns=status, margins=True, dropna=False) (b)
# Why a second attempt: attempt a (qcut on edge values) gave DTYPE_ONLY
import pandas as pd
df = pd.read_csv("tickets.csv")
result = pd.pivot_table(df, values="amount", index="category", columns="status", aggfunc="sum", margins=True, dropna=False)
