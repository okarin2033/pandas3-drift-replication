# VERIFY control num_zero_vs_nonzero (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: VALUE_DRIFT.
# exactly one of a, b is 0 -> relative difference 1 -> SUBSTANTIVE (absolute 1e-7 > 1e-9, so it is drift)
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (0.0) if V < 3 else (1e-7)
