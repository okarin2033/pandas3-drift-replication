# VERIFY control num_text_differs (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: VALUE_DRIFT.
# text compared exactly
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
result = ("abc") if V < 3 else ("abd")
