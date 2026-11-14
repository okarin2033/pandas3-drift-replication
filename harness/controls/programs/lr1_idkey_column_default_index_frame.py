# REPAIR5 control lr1_idkey_column_default_index_frame (hand-written, synthetic data; 2026-11-11, lead ruling LR1.4). Expected class: ORDER_DRIFT.
# LR1.4 must be ORDER_DRIFT (table form): identity key __index__, the key (city) held as a column, default index 0..n-1, rows reordered beyond ties (cities distinct); LR1.2 uses the whole row as the key
import pandas as pd
df = pd.read_csv("people2.csv")
result = df[["city"]].value_counts(sort=False).reset_index(name="n")
