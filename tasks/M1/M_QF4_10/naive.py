# M_QF4_10 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

df = pd.read_csv("subscribers.csv")
counts = df.groupby(df["tier"].str.strip().str.lower(), as_index=False)["subscriber_id"].count()
result = counts.rename(columns={"subscriber_id": "subscribers"})
