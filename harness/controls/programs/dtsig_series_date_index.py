# REPAIR control dtsig_series_date_index (hand-written, synthetic data; 2026-11-11, review MF5). Expected class: DTYPE_ONLY.
# dtype_significant card; integer values unchanged, only the unit of the parsed date index changes: not DTYPE_DRIFT
import pandas as pd
result = pd.read_csv("left.csv", parse_dates=["date"], index_col="date")["value"]
