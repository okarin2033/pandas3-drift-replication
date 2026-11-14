# VERIFY control num_frame_one_large_cell (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: VALUE_DRIFT.
# one cell differs by 1%: SUBSTANTIVE although another cell differs by 1e-8
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (pd.DataFrame({"a": [1.0, 2.0, 3.0], "b": [10.0, 20.0, 30.0]})) if V < 3 else (pd.DataFrame({"a": [1.0 * (1 + 1e-8), 2.0, 3.0], "b": [10.0, 20.0, 30.0 * 1.01]}))
