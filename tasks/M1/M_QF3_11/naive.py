# M_QF3_11 naive solution (invited idiom, section 4.4a). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import pandas as pd

orig = pd.read_csv("admissions.csv")
orig["ward"] = orig["ward"].str.strip().str.lower()
filled = orig.rename(columns={"charge": "charge_eur"}, copy=False)
filled.loc[filled["charge_eur"].isna(), "charge_eur"] = 0.0
result = pd.DataFrame({
    "mean_known": orig.groupby("ward")["charge"].mean().round(2),
    "mean_zero_filled": filled.groupby("ward")["charge_eur"].mean().round(2),
})
