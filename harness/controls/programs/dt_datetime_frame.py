# VERIFY control dt_datetime_frame (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: DTYPE_ONLY.
# parsed dates are datetime64[ns] on 2.3.3 and a coarser unit on 3.x; canonical timestamps equal
import pandas as pd
df = pd.read_csv("people.csv", parse_dates=["signup"])
result = df[["id", "signup"]]
