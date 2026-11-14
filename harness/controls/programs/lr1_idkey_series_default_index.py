# REPAIR5 control lr1_idkey_series_default_index (hand-written, synthetic data; 2026-11-11, lead ruling LR1.4). Expected class: ORDER_DRIFT.
# Series form (LR1.2, review RV-2(c); added next to the two LR1.4 forms): the counts as a Series with a default index, values reordered beyond ties (3 moves from first to last); the whole row is the key
import pandas as pd
df = pd.read_csv("people2.csv")
result = df[["city"]].value_counts(sort=False).reset_index(name="n")["n"]
