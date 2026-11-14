# REPAIR2 control idkey_same_order_file_rows (hand-written, synthetic data; 2026-11-11, Amendment 3). Expected class: DTYPE_ONLY.
# order_significant with the identity key __index__ on a file-order result (default row labels 0..n-1 kept in file order on every version); text columns change dtype only: not ORDER_DRIFT
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["name", "city"]]
