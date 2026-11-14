# VERIFY control num_identical_float (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: IDENTICAL.
# same value
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = (2.5) if V < 3 else (2.5)
