# VERIFY control ord_dataframe_value_counts_frame (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_ONLY.
# the same as a DataFrame with a default index (index ignored by the oracle)
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["plan", "city"]].value_counts(sort=False).reset_index(name="n")
