# M_QF1_01 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("members.csv")
for col in df.columns:
    if df[col].dtype == object:
        df[col] = df[col].str.strip().str.title()
df = df[df["home_city"].notna() & (df["home_city"] != "-")]
result = (df.groupby("home_city")
            .agg(members=("member_id", "count"), total_fee=("fee", "sum"))
            .reset_index())
