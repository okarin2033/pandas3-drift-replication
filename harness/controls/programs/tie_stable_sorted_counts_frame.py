# VERIFY control tie_stable_sorted_counts_frame (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_ONLY.
# same, as a DataFrame with key column n
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["plan", "city"]].value_counts(sort=False).sort_values(ascending=False, kind="stable").reset_index(name="n")
