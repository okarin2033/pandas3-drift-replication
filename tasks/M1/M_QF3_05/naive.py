# M_QF3_05 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import numpy as np
import pandas as pd

raw = pd.read_csv("gauges.csv")
raw["site"] = raw["site"].str.strip().str.lower()
clean = raw.astype({"reading": "float64"}, copy=False)
clean.loc[clean["level"] > 60, "reading"] = np.nan
result = pd.DataFrame({
    "raw_mean": raw.groupby("site")["reading"].mean().round(3),
    "clean_mean": clean.groupby("site")["reading"].mean().round(3),
})
