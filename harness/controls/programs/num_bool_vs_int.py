# VERIFY control num_bool_vs_int (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: DTYPE_ONLY.
# booleans treated as 0/1: dtype difference only
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (pd.DataFrame({"a": [True, False, True]})) if V < 3 else (pd.DataFrame({"a": [1, 0, 1]}))
