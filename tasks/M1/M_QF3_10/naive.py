# M_QF3_10 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

def fill_gaps(frame):
    return frame.ffill(inplace=True)

df = pd.read_csv("gauges.csv")
result = fill_gaps(df)
