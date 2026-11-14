# VERIFY control num_below_relative_tol (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: IDENTICAL.
# relative difference 1e-12 < 1e-11
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (2.5) if V < 3 else (2.5 * (1 + 1e-12))
