# REPAIR5 control lr1_namedkey_index_ties_only (hand-written, synthetic data; 2026-11-11, lead ruling LR1.4). Expected class: ORDER_ONLY.
# LR1.4 must be ORDER_ONLY: named key n held in the index (not a column), rows permuted among ties only (stable descending sort by n; only the cities inside the count-2 block change places); LR1.1 finds n among the index level names
import pandas as pd
df = pd.read_csv("people2.csv")
result = df[["city"]].value_counts(sort=False).sort_values(ascending=False, kind="stable").reset_index(name="n").set_index("n")
