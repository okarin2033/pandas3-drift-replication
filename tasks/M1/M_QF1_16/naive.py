# M_QF1_16 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("price_list.csv")
text_cols = df.dtypes[df.dtypes == object].index
for c in text_cols:
    df[c] = df[c].str.strip().str.upper()
result = df.sort_values("sku").reset_index(drop=True)
