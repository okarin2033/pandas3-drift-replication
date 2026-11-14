# REPAIR6 control lr16_key_not_found_reordered (hand-written, synthetic data; 2026-11-12, lead ruling LR16). Expected class: ORDER_DRIFT.
# LR16 (b) case: named sort key total is neither a column nor an index level name of the result; rows reordered: under LR1 HRUN H1 ("sort key not found") ORDER_DRIFT; under the LR16 (b) sensitivity ORDER_ONLY
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["plan", "city"]].value_counts(sort=False).reset_index(name="n")
