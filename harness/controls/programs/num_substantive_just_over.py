# VERIFY control num_substantive_just_over (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: VALUE_DRIFT.
# relative difference 2e-6 >= 1e-6
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (1.0) if V < 3 else (1.0 + 2e-6)
