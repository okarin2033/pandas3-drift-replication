# MECH_A confirm program S05 (attempt 1). drafted_by: pkg:MECH_A, 2026-11-11. Own code, synthetic data.
# Idea (catalogue): regex word class on non-ASCII names (first word of each name).
import pandas as pd

df = pd.read_csv("people.csv")
df["first_word"] = df["name"].str.extract(r"^(\w+)", expand=False)
result = df[["person_id", "first_word"]]
