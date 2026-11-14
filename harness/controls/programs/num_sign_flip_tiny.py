# VERIFY control num_sign_flip_tiny (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: VALUE_DRIFT.
# relative difference 2 (opposite signs), absolute 2e-8 > 1e-9
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (1e-8) if V < 3 else (-1e-8)
