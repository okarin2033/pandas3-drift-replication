# VERIFY control num_below_absolute_tol (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: IDENTICAL.
# one zero but absolute difference 1e-12 < 1e-9: equal by the oracle tolerance
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (0.0) if V < 3 else (1e-12)
