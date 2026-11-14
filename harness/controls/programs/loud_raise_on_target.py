# VERIFY control loud_raise_on_target (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: LOUD.
# the 3.x run raises: LOUD, never drift
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
if V >= 3:
    raise ValueError("control: target raises")
result = 1
