# REPAIR2 control idkey_same_order_groupby (hand-written, synthetic data; 2026-11-11, Amendment 3). Expected class: DTYPE_ONLY.
# order_significant with the identity key __index__; groupby sorts its text keys on every version, so the index label at every row position is the same; only the label and text dtypes change: not ORDER_DRIFT
import pandas as pd
df = pd.read_csv("people.csv")
result = df.groupby("city")[["amount"]].sum()
