# Task specifications for family QF2_DATETIME (stratum M, package TASKS_M1).
# Written 2026-11-11 by pkg:TASKS_M1; drafted_by pkg:TASKS_M1, status prepared.

FAMILY = 'QF2_DATETIME'

TASKS = [
# ------------------------------------------------------------------ D01 (slots 01, 11)
dict(
 id='M_QF2_01', row='D01', invited=['D01'], files=['QF2_DATETIME/signups.csv'],
 text=("For each sign-up channel (written in lower case without surrounding spaces; rows without a channel are left out), "
       "give the first and the last sign-up day as Unix timestamps in seconds (midnight UTC of that day). `result` should be a "
       "table indexed by channel with the columns first_signup and last_signup (whole numbers)."),
 allowed=['Unix timestamps in seconds', 'midnight UTC'], order=False, keys=[],
 intended=("Parse signup_day, clean channel (4 channels), and per channel return the minimum and maximum sign-up day as "
           "seconds since 1970-01-01 00:00 UTC (values between 2023-01-01 and 2026-01-01, i.e. 1672531200-1767225600)."),
 notes='channel may be a column instead of the index.',
 checks=[('n_groups_equals', {'n': 4}),
         ('numeric_in_range', {'columns': ['first_signup', 'last_signup'], 'min': 1672531200, 'max': 1767225600})],
 direction='HARM', reason='on 3.x parsed dates are stored at a coarser unit, so the integer cast divided by 10**9 gives numbers 1000 times too small',
 naive='''import pandas as pd

df = pd.read_csv("signups.csv")
df = df.dropna(subset=["channel"])
df["channel"] = df["channel"].str.strip().str.lower()
df["signup_day"] = pd.to_datetime(df["signup_day"])
df["unix_s"] = df["signup_day"].astype("int64") // 10**9
result = df.groupby("channel")["unix_s"].agg(first_signup="min", last_signup="max")
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("signups.csv")
first, last = {}, {}
epoch = dt.date(1970, 1, 1)
for ch, day in zip(df["channel"].tolist(), df["signup_day"].tolist()):
    if not isinstance(ch, str):
        continue
    k = ch.strip().lower()
    secs = (dt.date.fromisoformat(day) - epoch).days * 86400
    first[k] = min(first.get(k, secs), secs)
    last[k] = max(last.get(k, secs), secs)
keys = sorted(first)
result = pd.DataFrame({"first_signup": [first[k] for k in keys], "last_signup": [last[k] for k in keys]},
                      index=pd.Index(keys)).astype("int64")
'''),
dict(
 id='M_QF2_11', row='D01', invited=['D01'], files=['QF2_DATETIME/sessions.csv'],
 text=("Put the sessions in time order of started_at and compute the gap in seconds between each session start and the "
       "previous one. `result` should be the median gap in seconds (a float)."),
 allowed=['seconds'], order=False, keys=[],
 intended=("Parse started_at, sort ascending, take the differences between consecutive starts in seconds (249 gaps) and "
           "return their median as a float."),
 notes='',
 checks=[('result_kind', {'kind': 'scalar'}), ('numeric_in_range', {'columns': ['__values__'], 'min': 60, 'max': 86400})],
 direction='HARM', reason='on 3.x the integer cast of parsed timestamps is in a coarser unit, so dividing by 1e9 gives gaps 1000 times too small',
 naive='''import pandas as pd

df = pd.read_csv("sessions.csv")
t = pd.to_datetime(df["started_at"]).sort_values()
secs = t.astype("int64") / 1e9
result = float(secs.diff().median())
''',
 ref='''import datetime as dt
import statistics
import pandas as pd

df = pd.read_csv("sessions.csv")
ts = sorted(dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S") for s in df["started_at"].tolist())
gaps = [(b - a).total_seconds() for a, b in zip(ts[:-1], ts[1:])]
result = float(statistics.median(gaps))
'''),
# ------------------------------------------------------------------ D02 (slots 02, 12)
dict(
 id='M_QF2_02', row='D02', invited=['D02'], files=['QF2_DATETIME/clicks.csv'],
 text=("Round each click time given in epoch_s down to the start of its minute. `result` should be a table with the "
       "columns click_ref (written as in the file, seven digits with leading zeros) and minute_start (the rounded time as a "
       "Unix timestamp in seconds), in file order."),
 allowed=['Unix timestamp in seconds', 'leading zeros'], order=False, keys=[],
 intended=("Keep click_ref as text; for each of the 500 clicks compute epoch_s rounded down to a multiple of 60 seconds and "
           "return click_ref and minute_start in file order (values in April-July 2025, 1743465600-1754006400)."),
 notes='',
 checks=[('n_groups_equals', {'n': 500}),
         ('numeric_in_range', {'columns': ['minute_start'], 'min': 1743465600, 'max': 1754006400})],
 direction='HARM', reason='on 3.x the date-time made from seconds keeps a coarser unit, so the integer cast divided by 10**9 is wrong',
 naive='''import pandas as pd

df = pd.read_csv("clicks.csv", dtype={"click_ref": str})
ts = pd.to_datetime(df["epoch_s"], unit="s")
df["minute_start"] = ts.dt.floor("min").astype("int64") // 10**9
result = df[["click_ref", "minute_start"]]
''',
 ref='''import pandas as pd

df = pd.read_csv("clicks.csv", dtype={"click_ref": str})
mins = [int(s) // 60 * 60 for s in df["epoch_s"].tolist()]
result = pd.DataFrame({"click_ref": df["click_ref"].tolist(), "minute_start": mins})
result["minute_start"] = result["minute_start"].astype("int64")
'''),
dict(
 id='M_QF2_12', row='D02', invited=['D02'], files=['QF2_DATETIME/clicks.csv'],
 text=("Find the median moment at which the clicks were received, using epoch_ms (Unix time in milliseconds). `result` "
       "should be that moment as a timestamp (UTC, without time zone)."),
 allowed=['Unix time in milliseconds'], order=False, keys=[],
 intended=("Take the median of the 500 epoch_ms values (average of the two middle values) and return it as a timezone-naive "
           "UTC timestamp in 2025."),
 notes='sub-millisecond digits may be dropped.',
 checks=[('result_kind', {'kind': 'scalar'}),
         ('date_year_in_range', {'columns': ['__values__'], 'min_year': 2025, 'max_year': 2025})],
 direction='HARM', reason='on 3.x the integer cast of a date-time made from milliseconds is not in nanoseconds, so the median lands in 1970',
 naive='''import pandas as pd

df = pd.read_csv("clicks.csv")
ts = pd.to_datetime(df["epoch_ms"], unit="ms")
result = pd.to_datetime(ts.astype("int64").median())
''',
 ref='''import pandas as pd

df = pd.read_csv("clicks.csv")
ms = sorted(int(v) for v in df["epoch_ms"].tolist())
n = len(ms)
twice = ms[n // 2] * 2 if n % 2 else ms[n // 2 - 1] + ms[n // 2]
result = pd.Timestamp(twice * 500, unit="us")
'''),
# ------------------------------------------------------------------ D03 (slots 03, 13)
dict(
 id='M_QF2_03', row='D03', invited=['D03'], files=['QF2_DATETIME/shipments.csv'],
 text=("Total the order value per calendar month of ordered_on. Label each month by the moment at which the month ends (its "
       "last instant), not by its first day. `result` should be a Series indexed by that month-end moment with the summed "
       "value, in time order."),
 allowed=['month-end', 'last instant'], order=True, keys=['__index__'],
 intended=("Group the 400 shipments by the month of ordered_on (12 months of 2025), sum value per month and index each sum "
           "by the last instant of its month (e.g. 2025-01-31 23:59:59.999...), ascending."),
 notes='the last instant may be given to the second, millisecond, microsecond or nanosecond; month labels may be a column.',
 checks=[('n_groups_equals', {'n': 12}), ('date_year_in_range', {'columns': ['__index__'], 'min_year': 2025, 'max_year': 2025}),
         ('sorted_by', {'keys': ['__index__'], 'ascending': [True]})],
 direction='BOTH', reason='the month end moves from the last nanosecond to the last microsecond; both mark the end of the month',
 naive='''import pandas as pd

df = pd.read_csv("shipments.csv")
month_end = pd.to_datetime(df["ordered_on"]).dt.to_period("M").dt.end_time
result = df.groupby(month_end)["value"].sum()
''',
 ref='''import math
import pandas as pd

df = pd.read_csv("shipments.csv")
tot = {}
for d, v in zip(df["ordered_on"].tolist(), df["value"].tolist()):
    y, m = int(d[:4]), int(d[5:7])
    tot.setdefault((y, m), []).append(float(v))
keys = sorted(tot)
ends = []
for y, m in keys:
    ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
    ends.append(pd.Timestamp(year=ny, month=nm, day=1).as_unit("ns") - pd.Timedelta(1, "ns"))
idx = pd.DatetimeIndex(ends).as_unit("ns")
result = pd.Series([round(math.fsum(tot[k]), 2) for k in keys], index=idx)
'''),
dict(
 id='M_QF2_13', row='D03', invited=['D03'], files=['QF2_DATETIME/quarterly_revenue.csv'],
 text=("For every quarter in the revenue file, report the moment at which the quarter closes (its last instant) together "
       "with the revenue. `result` should be a table with the columns quarter_end and revenue, oldest quarter first."),
 allowed=['last instant'], order=True, keys=['quarter_end'],
 intended=("For each of the 30 quarters, compute the last instant of the quarter that starts at quarter_start (e.g. "
           "2019-03-31 23:59:59.999...) and return it with revenue, ascending by quarter_end."),
 notes='the last instant may be given to the second, millisecond, microsecond or nanosecond.',
 checks=[('n_groups_equals', {'n': 30}),
         ('date_year_in_range', {'columns': ['quarter_end'], 'min_year': 2019, 'max_year': 2026}),
         ('sorted_by', {'keys': ['quarter_end'], 'ascending': [True]})],
 direction='BOTH', reason='the quarter end moves from the last nanosecond to the last microsecond; both mark the close of the quarter',
 naive='''import pandas as pd

df = pd.read_csv("quarterly_revenue.csv")
df["quarter_end"] = pd.to_datetime(df["quarter_start"]).dt.to_period("Q").dt.end_time
result = df[["quarter_end", "revenue"]].sort_values("quarter_end").reset_index(drop=True)
''',
 ref='''import pandas as pd

df = pd.read_csv("quarterly_revenue.csv")
ends = []
for d in df["quarter_start"].tolist():
    y, m = int(d[:4]), int(d[5:7])
    m2 = m + 3
    ny, nm = (y + 1, m2 - 12) if m2 > 12 else (y, m2)
    ends.append(pd.Timestamp(year=ny, month=nm, day=1).as_unit("ns") - pd.Timedelta(1, "ns"))
out = pd.DataFrame({"quarter_end": pd.DatetimeIndex(ends).as_unit("ns"), "revenue": df["revenue"].astype("int64").tolist()})
result = out.sort_values("quarter_end", kind="mergesort").reset_index(drop=True)
'''),
# ------------------------------------------------------------------ D04 (slots 04, 14)
dict(
 id='M_QF2_04', row='D04', invited=['D04', 'D01'], files=['QF2_DATETIME/signups.csv'],
 text=("Count the sign-ups for every calendar day from the earliest to the latest sign-up day, including days with no "
       "sign-ups (count 0). Identify each day by its Unix timestamp in seconds (midnight UTC). `result` should be a Series "
       "indexed by that number with the counts, in day order."),
 allowed=['Unix timestamp in seconds', 'midnight UTC', 'calendar day'], order=True, keys=['__index__'],
 intended=("Build every day from 2023-01-05 to 2025-12-28 (1089 days), count the sign-ups per day (0 where none) and index "
           "the counts by the day's midnight UTC in seconds since 1970, ascending; counts add up to 300."),
 notes='the day key may be a column.',
 checks=[('n_groups_equals', {'n': 1089}), ('counts_sum_to_rows', {'column': '__values__', 'expected': 300}),
         ('numeric_in_range', {'columns': ['__index__'], 'min': 1672531200, 'max': 1767225600}),
         ('sorted_by', {'keys': ['__index__'], 'ascending': [True]})],
 direction='HARM', reason='on 3.x the generated day range uses a coarser unit, so the integer cast divided by 10**9 is not Unix seconds',
 naive='''import pandas as pd

df = pd.read_csv("signups.csv")
df["signup_day"] = pd.to_datetime(df["signup_day"])
days = pd.date_range(df["signup_day"].min(), df["signup_day"].max(), freq="D")
counts = df["signup_day"].value_counts().reindex(days, fill_value=0)
counts.index = days.astype("int64") // 10**9
result = counts
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("signups.csv")
days = [dt.date.fromisoformat(s) for s in df["signup_day"].tolist()]
first, last = min(days), max(days)
cnt = {}
for d in days:
    cnt[d] = cnt.get(d, 0) + 1
epoch = dt.date(1970, 1, 1)
keys, vals = [], []
d = first
while d <= last:
    keys.append((d - epoch).days * 86400)
    vals.append(cnt.get(d, 0))
    d += dt.timedelta(days=1)
result = pd.Series(vals, index=pd.Index(keys, dtype="int64"), dtype="int64")
'''),
dict(
 id='M_QF2_14', row='D04', invited=['D04', 'D01'], files=['QF2_DATETIME/shipments.csv'],
 text=("Between the first and the last order date (both included), which calendar days had no orders at all? Give each such "
       "day as a day number counted from 1970-01-01 (that date is day 0). `result` should be a sorted Python list of these "
       "day numbers."),
 allowed=['calendar days', 'day number'], order=True, keys=['__values__'],
 intended=("List every day from 2025-01-02 to 2025-12-19 on which no shipment was ordered (117 days) as the number of days "
           "since 1970-01-01 (2025-01-02 is day 20090), sorted ascending."),
 notes='',
 checks=[('n_groups_equals', {'n': 117}), ('numeric_in_range', {'columns': ['__values__'], 'min': 20090, 'max': 20441}),
         ('sorted_by', {'keys': ['__values__'], 'ascending': [True]})],
 direction='HARM', reason='on 3.x the generated day range uses a coarser unit, so integer division by a nanosecond day gives wrong day numbers',
 naive='''import pandas as pd

df = pd.read_csv("shipments.csv")
d = pd.to_datetime(df["ordered_on"])
all_days = pd.date_range(d.min(), d.max(), freq="D")
missing = all_days.difference(pd.DatetimeIndex(d.unique()))
result = sorted((missing.astype("int64") // (86400 * 10**9)).tolist())
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("shipments.csv")
have = {dt.date.fromisoformat(s) for s in df["ordered_on"].tolist()}
epoch = dt.date(1970, 1, 1)
out = []
d = min(have)
while d <= max(have):
    if d not in have:
        out.append((d - epoch).days)
    d += dt.timedelta(days=1)
result = out
'''),
# ------------------------------------------------------------------ D05 (slots 05, 15)
dict(
 id='M_QF2_05', row='D05', invited=['D05'], files=['QF2_DATETIME/appointments.csv'],
 text=("Each appointment needs a reminder exactly one calendar day before it, at the same New York wall-clock time "
       "(local_start is New York local time). `result` should be a table with the columns appt_id and reminder, where "
       "reminder is ISO 8601 text including the UTC offset that applies in New York at the reminder time (for example "
       "'2025-06-12T08:45:00-04:00'), in file order."),
 allowed=['ISO 8601', 'UTC offset', 'wall-clock time', 'New York'], order=False, keys=[],
 intended=("For each of the 160 appointments take the New York wall-clock start minus one calendar day and write it as ISO "
           "text with the offset valid in New York at that moment (-05:00 in winter, -04:00 in summer)."),
 notes='',
 checks=[('n_groups_equals', {'n': 160}),
         ('date_year_in_range', {'columns': ['reminder'], 'min_year': 2025, 'max_year': 2025})],
 direction='FIX', reason='with the 2.x time-zone library the stdlib date arithmetic keeps the old UTC offset across the clock change; 3.x gives the correct offset',
 naive='''from datetime import timedelta
import pandas as pd

df = pd.read_csv("appointments.csv")
start = pd.to_datetime(df["local_start"]).dt.tz_localize("America/New_York")
df["reminder"] = start.map(lambda t: (t.to_pydatetime() - timedelta(days=1)).isoformat())
result = df[["appt_id", "reminder"]]
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("appointments.csv")
local = [dt.datetime.strptime(s, "%Y-%m-%d %H:%M") - dt.timedelta(days=1) for s in df["local_start"].tolist()]
aware = pd.DatetimeIndex(local).tz_localize("America/New_York")
result = pd.DataFrame({"appt_id": df["appt_id"].astype("int64").tolist(), "reminder": [t.isoformat() for t in aware]})
'''),
dict(
 id='M_QF2_15', row='D05', invited=['D05'], files=['QF2_DATETIME/appointments.csv'],
 text=("Every appointment gets a follow-up visit four weeks later at the same New York wall-clock time (local_start is New "
       "York local time). `result` should be a table with the columns appt_id and follow_up_utc, the follow-up time "
       "converted to UTC and written as text 'YYYY-MM-DD HH:MM', in file order."),
 allowed=['wall-clock time', 'New York', 'UTC'], order=False, keys=[],
 intended=("Add 28 calendar days to each New York wall-clock start (160 appointments), localise to New York and convert to "
           "UTC, written as 'YYYY-MM-DD HH:MM'."),
 notes='',
 checks=[('n_groups_equals', {'n': 160}),
         ('date_year_in_range', {'columns': ['follow_up_utc'], 'min_year': 2025, 'max_year': 2025})],
 direction='FIX', reason='with the 2.x time-zone library adding weeks to a stdlib datetime keeps the old offset, so UTC is off by one hour across the clock change',
 naive='''from datetime import timedelta, timezone
import pandas as pd

df = pd.read_csv("appointments.csv")
start = pd.to_datetime(df["local_start"]).dt.tz_localize("America/New_York")
df["follow_up_utc"] = start.map(
    lambda t: (t.to_pydatetime() + timedelta(weeks=4)).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M"))
result = df[["appt_id", "follow_up_utc"]]
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("appointments.csv")
local = [dt.datetime.strptime(s, "%Y-%m-%d %H:%M") + dt.timedelta(days=28) for s in df["local_start"].tolist()]
utc = pd.DatetimeIndex(local).tz_localize("America/New_York").tz_convert("UTC")
result = pd.DataFrame({"appt_id": df["appt_id"].astype("int64").tolist(),
                       "follow_up_utc": [t.strftime("%Y-%m-%d %H:%M") for t in utc]})
'''),
# ------------------------------------------------------------------ D06 (slots 06, 16)
dict(
 id='M_QF2_06', row='D06', invited=['D06'], files=['QF2_DATETIME/appointments.csv'],
 text=("Offer every patient a slot on the next calendar day at the same New York wall-clock time as their appointment "
       "(local_start is New York local time). `result` should be a table with the columns appt_id and next_day_slot, the "
       "slot as New York local time text 'YYYY-MM-DD HH:MM', in file order."),
 allowed=['calendar day', 'wall-clock time', 'New York'], order=False, keys=[],
 intended="For each of the 160 appointments return the same local clock time one calendar day later as 'YYYY-MM-DD HH:MM'.",
 notes='',
 checks=[('n_groups_equals', {'n': 160}),
         ('date_year_in_range', {'columns': ['next_day_slot'], 'min_year': 2025, 'max_year': 2025})],
 direction='FIX', reason='on 2.x the day offset adds 24 hours, which shifts the wall-clock time across the clock change; 3.x adds a calendar day',
 naive='''import pandas as pd

df = pd.read_csv("appointments.csv")
start = pd.to_datetime(df["local_start"]).dt.tz_localize("America/New_York")
slot = start + pd.offsets.Day(1)
df["next_day_slot"] = slot.dt.strftime("%Y-%m-%d %H:%M")
result = df[["appt_id", "next_day_slot"]]
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("appointments.csv")
slots = [(dt.datetime.strptime(s, "%Y-%m-%d %H:%M") + dt.timedelta(days=1)).strftime("%Y-%m-%d %H:%M")
         for s in df["local_start"].tolist()]
result = pd.DataFrame({"appt_id": df["appt_id"].astype("int64").tolist(), "next_day_slot": slots})
'''),
dict(
 id='M_QF2_16', row='D06', invited=['D06'], files=['QF2_DATETIME/appointments.csv'],
 text=("For each appointment a check-up is booked 14 calendar days later at the same New York wall-clock time (local_start "
       "is New York local time). Count how many check-ups start in each hour of the New York day. `result` should be a "
       "Series indexed by hour (0-23) with the number of check-ups, only for hours that occur."),
 allowed=['calendar days', 'wall-clock time', 'New York'], order=False, keys=[],
 intended=("The check-up keeps the local clock time, so its local hour equals the appointment's hour; count the 160 "
           "check-ups per local hour."),
 notes='hour may be a column with a count column.',
 checks=[('counts_sum_to_rows', {'column': '__values__', 'expected': 160}),
         ('numeric_in_range', {'columns': ['__index__'], 'min': 0, 'max': 23})],
 direction='FIX', reason='on 2.x the day offset adds 14 x 24 hours, so check-ups across the clock change land one hour off; 3.x keeps the local hour',
 naive='''import pandas as pd

df = pd.read_csv("appointments.csv")
start = pd.to_datetime(df["local_start"]).dt.tz_localize("America/New_York")
checkup = start + pd.offsets.Day(14)
result = checkup.dt.hour.value_counts().sort_index()
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("appointments.csv")
cnt = {}
for s in df["local_start"].tolist():
    h = (dt.datetime.strptime(s, "%Y-%m-%d %H:%M") + dt.timedelta(days=14)).hour
    cnt[h] = cnt.get(h, 0) + 1
keys = sorted(cnt)
result = pd.Series([cnt[k] for k in keys], index=pd.Index(keys, dtype="int64"), dtype="int64")
'''),
# ------------------------------------------------------------------ D07 (slot 07)
dict(
 id='M_QF2_07', row='D07', invited=['D07'], files=['QF2_DATETIME/clicks.csv'],
 text=("Read the clicks file keeping every column as text, so that click_ref keeps its leading zeros. Then turn epoch_s "
       "(Unix time in seconds) into a date-time, treating values that cannot be converted as missing, and count the clicks "
       "per calendar day (UTC). `result` should be a Series indexed by day (text 'YYYY-MM-DD') with the click counts, in "
       "day order."),
 allowed=['Unix time in seconds', 'leading zeros', 'UTC'], order=True, keys=['__index__'],
 intended=("All epoch_s values are valid whole numbers, so every click converts; count the 500 clicks per UTC calendar day "
           "and index the counts by 'YYYY-MM-DD', ascending."),
 notes='',
 checks=[('counts_sum_to_rows', {'column': '__values__', 'expected': 500}),
         ('date_year_in_range', {'columns': ['__index__'], 'min_year': 2025, 'max_year': 2025}),
         ('sorted_by', {'keys': ['__index__'], 'ascending': [True]})],
 direction='HARM', reason='on 3.x digit strings given with a seconds unit are parsed as date text, fail and become missing, so no clicks are counted',
 naive='''import pandas as pd

df = pd.read_csv("clicks.csv", dtype=str)
ts = pd.to_datetime(df["epoch_s"], unit="s", errors="coerce")
result = ts.dt.strftime("%Y-%m-%d").value_counts().sort_index()
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("clicks.csv", dtype=str)
cnt = {}
for s in df["epoch_s"].tolist():
    try:
        day = dt.datetime.fromtimestamp(int(s), tz=dt.timezone.utc).strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        continue
    cnt[day] = cnt.get(day, 0) + 1
keys = sorted(cnt)
result = pd.Series([cnt[k] for k in keys], index=pd.Index(keys), dtype="int64")
'''),
# ------------------------------------------------------------------ D08 (slot 08)
dict(
 id='M_QF2_08', row='D08', invited=['D08'], files=['QF2_DATETIME/shipments.csv'],
 text=("Read the shipments file with both date columns parsed as dates. Then, for every date column in the table, replace "
       "the date by the number of days since 2025-01-01 (missing dates stay missing). `result` should be the whole table with "
       "the converted columns."),
 allowed=['date columns', 'days since'], order=False, keys=[],
 intended=("Convert ordered_on and shipped_on to whole days since 2025-01-01 (shipped_on empty for 16 rows stays missing), "
           "keep the other columns unchanged, 400 rows in file order."),
 notes='the day counts may be integers or floats.',
 checks=[('n_groups_equals', {'n': 400}),
         ('numeric_in_range', {'columns': ['ordered_on', 'shipped_on'], 'min': 0, 'max': 400}),
         ('columns_present', {'columns': ['shipment_id', 'ordered_on', 'shipped_on', 'carrier', 'weight_kg', 'value']})],
 direction='HARM', reason="on 3.1 the type name 'datetime64[ns]' no longer matches the parsed date columns, so nothing is converted",
 naive='''import pandas as pd

df = pd.read_csv("shipments.csv", parse_dates=["ordered_on", "shipped_on"])
base = pd.Timestamp("2025-01-01")
for c in df.select_dtypes(include="datetime64[ns]").columns:
    df[c] = (df[c] - base).dt.days
result = df
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("shipments.csv")
base = dt.date(2025, 1, 1)
def days(v):
    return float((dt.date.fromisoformat(v) - base).days) if isinstance(v, str) else float("nan")
out = pd.DataFrame({
    "shipment_id": df["shipment_id"].astype("int64").tolist(),
    "ordered_on": [days(v) for v in df["ordered_on"].tolist()],
    "shipped_on": [days(v) for v in df["shipped_on"].tolist()],
    "carrier": df["carrier"].tolist(),
    "weight_kg": df["weight_kg"].tolist(),
    "value": df["value"].tolist(),
})
result = out
'''),
# ------------------------------------------------------------------ D09 (slot 09)
dict(
 id='M_QF2_09', row='D09', invited=['D09'], files=['QF2_DATETIME/quarterly_revenue.csv'],
 text=("The quarter_start dates should form a regular calendar series. Let pandas work out the spacing of these dates and "
       "report it as a frequency alias. `result` should be that alias (a short text code)."),
 allowed=['frequency alias'], order=False, keys=[],
 intended=("The dates are consecutive quarter starts (1 January, 1 April, 1 July, 1 October), so the answer is the alias "
           "for quarterly spacing anchored on quarter starts."),
 notes="any alias that means quarter-start spacing on calendar quarters is acceptable: 'QS', 'QS-JAN', 'QS-APR', 'QS-JUL' or 'QS-OCT'.",
 checks=[('result_kind', {'kind': 'scalar'}),
         ('values_in_set', {'column': '__values__', 'values': ['QS', 'QS-JAN', 'QS-APR', 'QS-JUL', 'QS-OCT']})],
 direction='BOTH', reason="3.1 reports the anchor month January instead of October; both aliases describe the same calendar-quarter starts",
 naive='''import pandas as pd

df = pd.read_csv("quarterly_revenue.csv")
result = pd.infer_freq(pd.to_datetime(df["quarter_start"]))
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("quarterly_revenue.csv")
days = [dt.date.fromisoformat(s) for s in df["quarter_start"].tolist()]
ok = all(d.day == 1 and d.month in (1, 4, 7, 10) for d in days)
steps = [(b.year * 12 + b.month) - (a.year * 12 + a.month) for a, b in zip(days[:-1], days[1:])]
result = "QS-JAN" if ok and steps and all(s == 3 for s in steps) else None
'''),
# ------------------------------------------------------------------ D10 (slot 10)
dict(
 id='M_QF2_10', row='D10', invited=['D10'], files=['QF2_DATETIME/sessions.csv'],
 text=("Find the start time of the earliest session in the file. `result` should be that start time as a standard-library "
       "datetime.datetime value."),
 allowed=['datetime.datetime'], order=False, keys=[],
 intended="Parse started_at and return the minimum (2025-06-01 05:07:33) as a datetime.datetime.",
 notes='',
 checks=[('result_kind', {'kind': 'scalar'}),
         ('date_year_in_range', {'columns': ['__values__'], 'min_year': 2025, 'max_year': 2025})],
 direction='HARM', reason='on 3.x the conversion returns a Series that keeps the original labels, so [0] picks the first row of the file, not the earliest',
 naive='''import pandas as pd

df = pd.read_csv("sessions.csv")
df["started_at"] = pd.to_datetime(df["started_at"])
df = df.sort_values("started_at")
result = df["started_at"].dt.to_pydatetime()[0]
''',
 ref='''import datetime as dt
import pandas as pd

df = pd.read_csv("sessions.csv")
result = min(dt.datetime.strptime(s, "%Y-%m-%d %H:%M:%S") for s in df["started_at"].tolist())
'''),
]
