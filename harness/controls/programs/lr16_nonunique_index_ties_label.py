# REPAIR6 control lr16_nonunique_index_ties_label (hand-written, synthetic data; 2026-11-12, lead ruling LR16). Expected class: ORDER_ONLY.
# LR16 (a) case: identity key __index__ on a non-unique index (plan; two rows per plan after a stable sort by plan); only rows that share a plan label change places, so under LR1 (key = index labels) the order differs only in ties: ORDER_ONLY; under the LR16 (a) sensitivity (whole row as key) ORDER_DRIFT
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["plan", "city"]].value_counts(sort=False).reset_index(name="n").set_index("plan").sort_index(kind="stable")
