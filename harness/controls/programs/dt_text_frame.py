# VERIFY control dt_text_frame (hand-written, synthetic data; pkg:VERIFY 2026-11-11). Expected class: DTYPE_ONLY.
# text columns are object on 2.3.3 and str on 3.x; values equal; unflagged -> DTYPE_ONLY
import pandas as pd
df = pd.read_csv("people.csv")
result = df[["name", "city", "plan"]]
