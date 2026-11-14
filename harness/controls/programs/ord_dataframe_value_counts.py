# VERIFY control ord_dataframe_value_counts (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: ORDER_ONLY.
# DataFrame.value_counts(sort=False) lists groups sorted on 2.3.3 and in first-appearance order on 3.x; unflagged -> ORDER_ONLY
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["plan", "city"]].value_counts(sort=False)
