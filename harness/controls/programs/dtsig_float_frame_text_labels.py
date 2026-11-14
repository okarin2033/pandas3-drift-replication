# REPAIR control dtsig_float_frame_text_labels (hand-written, synthetic data; 2026-11-11, review MF5). Expected class: DTYPE_ONLY.
# dtype_significant card; float cells are float64 on both sides, only the text row index and the column-label Index change object -> str: not DTYPE_DRIFT
import pandas as pd
df = pd.read_csv("people.csv")
result = df.groupby("city")[["amount"]].sum()
