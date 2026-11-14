# VERIFY control num_null_pattern (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: VALUE_DRIFT.
# null pattern differs
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (pd.DataFrame({"a": [1.0, float("nan"), 3.0]})) if V < 3 else (pd.DataFrame({"a": [1.0, 2.0, 3.0]}))
