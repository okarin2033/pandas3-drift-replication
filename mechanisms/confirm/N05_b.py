# MECH_B confirmation program N05 (attempt b), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df_nullable > threshold_series (b: NumPy-backed frame with missing cells against an Int64 Series)
# Why a second attempt: attempt a (frame already nullable via convert_dtypes) gave DTYPE_ONLY; the 3.1 note is about the frame falling back to NumPy
import pandas as pd
df = pd.read_csv("scores.csv")
threshold = pd.Series({"math": 5, "art": 3}, dtype="Int64")
result = df > threshold
