# VERIFY control num_frame_label_differs (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: VALUE_DRIFT.
# column label differs
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (pd.DataFrame({"a": [1.0, 2.0]})) if V < 3 else (pd.DataFrame({"b": [1.0, 2.0]}))
