# REPAIR5 control lr1_idkey_column_default_index_list (hand-written, synthetic data; 2026-11-11, lead ruling LR1.4). Expected class: ORDER_DRIFT.
# LR1.4 must be ORDER_DRIFT (list form): the same rows as a Python list of (city, n) tuples, reordered beyond ties; LR1.2 uses the element at each position
import pandas as pd
df = pd.read_csv("people2.csv")
result = list(df[["city"]].value_counts(sort=False).reset_index(name="n").itertuples(index=False, name=None))
