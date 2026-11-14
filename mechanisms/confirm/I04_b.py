# MECH_B confirmation program I04 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: logical op between Series with mismatched indexes (b)
# Why a second attempt: attempt a (mask & list) was LOUD (TypeError) on all 3.x configs
import pandas as pd
df = pd.read_csv("flags.csv")
paid_recent = df.loc[df.year > 2020, "paid"]
result = df.active & paid_recent
