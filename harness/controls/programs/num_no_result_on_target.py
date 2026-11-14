# VERIFY control num_no_result_on_target (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: NO_RESULT.
# the 3.x run completes without defining result: drift (NO_RESULT, section 3)
import pandas as pd
V = int(pd.__version__.split(".")[0])   # 2 = baseline (2.3.3), 3 = target (3.x)
if V < 3:
    result = 1
