# M_QF2_15 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("appointments.csv")
local = [dt.datetime.strptime(s, "%Y-%m-%d %H:%M") + dt.timedelta(days=28) for s in df["local_start"].tolist()]
utc = pd.DatetimeIndex(local).tz_localize("America/New_York").tz_convert("UTC")
result = pd.DataFrame({"appt_id": df["appt_id"].astype("int64").tolist(),
                       "follow_up_utc": [t.strftime("%Y-%m-%d %H:%M") for t in utc]})
