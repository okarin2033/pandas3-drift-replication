# MECH_A confirm program S05 (attempt 2, written after attempt 1 gave no value drift). drafted_by: pkg:MECH_A, 2026-11-11.
# Idea (catalogue): str.contains(r"^\w+$") on non-ASCII words (is the first name a single word?).
import pandas as pd

df = pd.read_csv("people.csv")
first = df["name"].str.split(" ").str[0]
df["first_is_word"] = first.str.contains(r"^\w+$")
result = df[["person_id", "first_is_word"]]
