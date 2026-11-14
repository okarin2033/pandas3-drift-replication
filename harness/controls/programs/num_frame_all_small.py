# VERIFY control num_frame_all_small (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: VALUE_DRIFT.
# same shape and labels, every differing cell numeric and below 1e-6 relative
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})) if V < 3 else (pd.DataFrame({"a": [1.0 * (1 + 1e-8), 2.0 * (1 + 2e-8), 3.0], "b": [10.0, 20.0 * (1 + 1e-7), 30.0 * (1 - 1e-8)]}))
