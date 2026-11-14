# MECH_B confirmation program I03 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: s[0] where the integer label exists but a position was meant (b: mixed text/integer labels)
# Why a second attempt: attempt a (text index) was LOUD (KeyError) on all 3.x configs
import pandas as pd
seats = pd.read_csv("seats.csv")
seats["seat"] = seats["seat"].map(lambda v: int(v) if v.isdigit() else v)
s = seats.set_index("seat").guest
result = s[0]
