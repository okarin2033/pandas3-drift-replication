# M_QF1_11 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
text_cols = [c for c in df.columns if pd.api.types.is_object_dtype(df[c])]
for c in text_cols:
    df[c] = df[c].str.strip().str.title()
result = int(df["full_name"].nunique())
