# MECH_B confirmation program N05 (attempt a), written 2026-11-11 by pkg:MECH_B; status: prepared.
# Catalogue idea: df_nullable > threshold_series
import pandas as pd
df = pd.read_csv("scores.csv").convert_dtypes()
threshold = pd.Series({"math": 5, "art": 3}, dtype="Int64")
result = df > threshold
