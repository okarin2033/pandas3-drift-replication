# M_QF2_06 reference solution (section 10.1). drafted_by: pkg:TASKS_M1; status: prepared. Written 2026-11-11.
import datetime as dt
import pandas as pd

df = pd.read_csv("appointments.csv")
slots = [(dt.datetime.strptime(s, "%Y-%m-%d %H:%M") + dt.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
         for s in df["local_start"].tolist()]
result = pd.DataFrame({"appt_id": df["appt_id"].astype("int64").tolist(), "next_day_slot": slots})
