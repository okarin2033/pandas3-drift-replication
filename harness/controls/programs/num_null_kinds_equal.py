# VERIFY control num_null_kinds_equal (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: IDENTICAL/DTYPE_ONLY.
# None, NaN and pd.NA are all null (section 3): no value difference
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (pd.DataFrame({"a": [1.0, None, 3.0]}, dtype="float64")) if V < 3 else (pd.DataFrame({"a": pd.array([1.0, pd.NA, 3.0], dtype="Float64")}))
