# VERIFY control tie_stable_sorted_counts_series (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_ONLY.
# sorted by count; every group has count 2, so the order differs only among ties of the key
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["plan", "city"]].value_counts(sort=False).sort_values(ascending=False, kind="stable")
