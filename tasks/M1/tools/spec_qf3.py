# Task specifications for family QF3_COW (stratum M, package TASKS_M1).
# Written 2026-11-11 by pkg:TASKS_M1; drafted_by pkg:TASKS_M1, status prepared.

FAMILY = 'QF3_COW'

_WARD = '''def tidy(v):
    return v.strip().lower()
'''

TASKS = [
# ------------------------------------------------------------------ C01 (slots 01, 07, 13)
dict(
 id='M_QF3_01', row='C01', invited=['C01'], files=['QF3_COW/bookings.csv'],
 text=("Cancelled bookings bring no revenue, so set their total to 0 (the state labels vary in capital letters and spaces). "
       "Then report the revenue per state, with the state names in lower case without surrounding spaces. `result` should be "
       "a Series indexed by state with the summed totals."),
 allowed=[], order=False, keys=[],
 intended=("Clean state (strip, lower; 4 states), set total to 0 for cancelled bookings and sum total per state; the "
           "cancelled state therefore has revenue 0."),
 notes='state may be a column; totals may be rounded to 2 decimals.',
 checks=[('n_groups_equals', {'n': 4}), ('no_nulls', {'columns': []})],
 direction='HARM', reason='on 3.x the two-step indexing assignment writes into a temporary, so cancelled totals are not set to 0',
 naive='''import pandas as pd

df = pd.read_csv("bookings.csv")
df["state"] = df["state"].str.strip().str.lower()
df["total"][df["state"] == "cancelled"] = 0
result = df.groupby("state")["total"].sum()
''',
 ref='''import pandas as pd

df = pd.read_csv("bookings.csv")
tot = {}
for st, t in zip(df["state"].tolist(), df["total"].tolist()):
    k = st.strip().lower()
    tot[k] = tot.get(k, 0.0) + (0.0 if k == "cancelled" else float(t))
keys = sorted(tot)
result = pd.Series([round(tot[k], 2) for k in keys], index=pd.Index(keys))
'''),
dict(
 id='M_QF3_07', row='C01', invited=['C01'], files=['QF3_COW/admissions.csv'],
 text=("Stays longer than 14 days are billed as 14 days. Apply that cap to stay_days and then give the average billed stay "
       "per ward (ward names in lower case without extra spaces), rounded to two decimals; missing stays are ignored. "
       "`result` should be a Series indexed by ward."),
 allowed=[], order=False, keys=[],
 intended=("Cap stay_days at 14, clean ward (5 wards) and return the mean capped stay per ward (missing stays skipped), "
           "rounded to 2 decimals; every value lies between 0 and 14."),
 notes='ward may be a column.',
 checks=[('n_groups_equals', {'n': 5}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': 14})],
 direction='HARM', reason='on 3.x the column-then-mask assignment does not reach the table, so stays are not capped',
 naive='''import pandas as pd

df = pd.read_csv("admissions.csv")
df["stay_days"][df["stay_days"] > 14] = 14
df["ward"] = df["ward"].str.strip().str.lower()
result = df.groupby("ward")["stay_days"].mean().round(2)
''',
 ref='''import pandas as pd

df = pd.read_csv("admissions.csv")
acc = {}
for w, s in zip(df["ward"].tolist(), df["stay_days"].tolist()):
    k = w.strip().lower()
    if pd.isna(s):
        acc.setdefault(k, [])
        continue
    acc.setdefault(k, []).append(min(float(s), 14.0))
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 2) for k in keys], index=pd.Index(keys))
'''),
dict(
 id='M_QF3_13', row='C01', invited=['C01'], files=['QF3_COW/gauges.csv'],
 text=("Readings taken at gauges whose alert level is above 60 are unreliable and must be treated as missing. After that, "
       "compute the mean reading per site (site names in lower case without extra spaces), rounded to three decimals. "
       "`result` should be a Series indexed by site."),
 allowed=[], order=False, keys=[],
 intended=("Set reading to missing where level > 60 (24 rows), clean site (3 sites) and return the mean of the remaining "
           "readings per site, rounded to 3 decimals."),
 notes='site may be a column.',
 checks=[('n_groups_equals', {'n': 3}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': None})],
 direction='HARM', reason='on 3.x the column-then-mask assignment is lost, so the unreliable readings stay in the means',
 naive='''import numpy as np
import pandas as pd

df = pd.read_csv("gauges.csv")
df["reading"][df["level"] > 60] = np.nan
df["site"] = df["site"].str.strip().str.lower()
result = df.groupby("site")["reading"].mean().round(3)
''',
 ref='''import pandas as pd

df = pd.read_csv("gauges.csv")
acc = {}
for site, r, lv in zip(df["site"].tolist(), df["reading"].tolist(), df["level"].tolist()):
    k = site.strip().lower()
    acc.setdefault(k, [])
    if not pd.isna(r) and int(lv) <= 60:
        acc[k].append(float(r))
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 3) for k in keys], index=pd.Index(keys))
'''),
# ------------------------------------------------------------------ C02 (slots 02, 08, 14)
dict(
 id='M_QF3_02', row='C02', invited=['C02'], files=['QF3_COW/admissions.csv'],
 text=("Fill each missing age with the median age of all admitted patients, then give the mean age per ward (ward names in "
       "lower case without extra spaces), rounded to one decimal. `result` should be a Series indexed by ward."),
 allowed=[], order=False, keys=[],
 intended=("Compute the median of the known ages, use it for the 12 missing ages, clean ward (5 wards) and return the mean "
           "age per ward rounded to 1 decimal."),
 notes='ward may be a column.',
 checks=[('n_groups_equals', {'n': 5}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': 120})],
 direction='HARM', reason='on 3.x filling the selected column with the in-place flag does not change the table, so missing ages stay out of the means',
 naive='''import pandas as pd

df = pd.read_csv("admissions.csv")
df["age"].fillna(df["age"].median(), inplace=True)
df["ward"] = df["ward"].str.strip().str.lower()
result = df.groupby("ward")["age"].mean().round(1)
''',
 ref='''import statistics
import pandas as pd

df = pd.read_csv("admissions.csv")
known = [float(a) for a in df["age"].tolist() if not pd.isna(a)]
med = statistics.median(known)
acc = {}
for w, a in zip(df["ward"].tolist(), df["age"].tolist()):
    acc.setdefault(w.strip().lower(), []).append(med if pd.isna(a) else float(a))
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 1) for k in keys], index=pd.Index(keys))
'''),
dict(
 id='M_QF3_08', row='C02', invited=['C02'], files=['QF3_COW/admissions.csv'],
 text=("A missing charge means that nothing was billed, i.e. 0. Taking that into account, compute the average charge per "
       "ward (ward names in lower case without extra spaces), rounded to two decimals. `result` should be a Series indexed "
       "by ward."),
 allowed=[], order=False, keys=[],
 intended=("Treat the 12 missing charges as 0, clean ward (5 wards) and return the mean charge per ward over all its "
           "admissions, rounded to 2 decimals."),
 notes='ward may be a column.',
 checks=[('n_groups_equals', {'n': 5}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': None})],
 direction='HARM', reason='on 3.x the in-place fill on the selected column is lost, so missing charges are skipped instead of counted as 0',
 naive='''import pandas as pd

df = pd.read_csv("admissions.csv")
df["charge"].fillna(0, inplace=True)
df["ward"] = df["ward"].str.strip().str.lower()
result = df.groupby("ward")["charge"].mean().round(2)
''',
 ref='''import pandas as pd

df = pd.read_csv("admissions.csv")
acc = {}
for w, c in zip(df["ward"].tolist(), df["charge"].tolist()):
    acc.setdefault(w.strip().lower(), []).append(0.0 if pd.isna(c) else float(c))
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 2) for k in keys], index=pd.Index(keys))
'''),
dict(
 id='M_QF3_14', row='C02', invited=['C02'], files=['QF3_COW/gauges.csv'],
 text=("The gauge log is in time order. Where a reading is missing, use the most recent earlier reading in the log. Then "
       "return the mean reading per site (site names in lower case without extra spaces), rounded to three decimals. "
       "`result` should be a Series indexed by site."),
 allowed=['most recent earlier reading'], order=False, keys=[],
 intended=("Forward-fill the 4 missing readings from the previous row of the log (the first row has a reading), clean "
           "site (3 sites) and return the mean reading per site rounded to 3 decimals."),
 notes='site may be a column.',
 checks=[('n_groups_equals', {'n': 3}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': None})],
 direction='HARM', reason='on 3.x the in-place forward fill on the selected column is lost, so the gaps stay empty',
 naive='''import pandas as pd

df = pd.read_csv("gauges.csv")
df["reading"].ffill(inplace=True)
df["site"] = df["site"].str.strip().str.lower()
result = df.groupby("site")["reading"].mean().round(3)
''',
 ref='''import pandas as pd

df = pd.read_csv("gauges.csv")
acc, last = {}, None
for site, r in zip(df["site"].tolist(), df["reading"].tolist()):
    if not pd.isna(r):
        last = float(r)
    acc.setdefault(site.strip().lower(), [])
    if last is not None:
        acc[site.strip().lower()].append(last)
keys = sorted(acc)
result = pd.Series([round(sum(acc[k]) / len(acc[k]), 3) for k in keys], index=pd.Index(keys))
'''),
# ------------------------------------------------------------------ C03 (slots 03, 09, 15)
dict(
 id='M_QF3_03', row='C03', invited=['C03'], files=['QF3_COW/bookings.csv'],
 text=("Refunded bookings have a negative total. For the revenue report, count every negative total as 0 and give the "
       "overall sum of the totals, rounded to two decimals. `result` should be that number."),
 allowed=[], order=False, keys=[],
 intended="Replace the 37 negative totals by 0 and return the sum of total over all 300 bookings, rounded to 2 decimals.",
 notes='',
 checks=[('result_kind', {'kind': 'scalar'}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': None})],
 direction='HARM', reason='on 3.x a write through a column taken out of the table no longer changes the table, so negatives stay in the sum',
 naive='''import pandas as pd

df = pd.read_csv("bookings.csv")
amounts = df["total"]
amounts[amounts < 0] = 0
result = round(df["total"].sum(), 2)
''',
 ref='''import math
import pandas as pd

df = pd.read_csv("bookings.csv")
result = round(math.fsum(max(float(t), 0.0) for t in df["total"].tolist()), 2)
'''),
dict(
 id='M_QF3_09', row='C03', invited=['C03'], files=['QF3_COW/admissions.csv'],
 text=("For privacy, ages above 85 must be reported as 85. Apply that rule to the age column, then give per ward (lower "
       "case, no extra spaces) the highest reported age and the number of patients whose reported age is 85. `result` should "
       "be a table indexed by ward with the columns max_age and patients_at_85."),
 allowed=[], order=False, keys=[],
 intended=("Cap age at 85 (40 patients are older), clean ward (5 wards) and per ward return the maximum capped age (at "
           "most 85) and the count of patients whose capped age equals 85."),
 notes='ward may be a column.',
 checks=[('n_groups_equals', {'n': 5}), ('numeric_in_range', {'columns': ['max_age'], 'min': 0, 'max': 85}),
         ('columns_present', {'columns': ['max_age', 'patients_at_85']})],
 direction='HARM', reason='on 3.x writing through the age column held in a separate variable does not reach the table, so ages stay uncapped',
 naive='''import pandas as pd

df = pd.read_csv("admissions.csv")
ages = df["age"]
ages[ages > 85] = 85
df["ward"] = df["ward"].str.strip().str.lower()
result = df.groupby("ward").agg(max_age=("age", "max"), patients_at_85=("age", lambda s: int((s == 85).sum())))
''',
 ref='''import pandas as pd

df = pd.read_csv("admissions.csv")
mx, n85 = {}, {}
for w, a in zip(df["ward"].tolist(), df["age"].tolist()):
    k = w.strip().lower()
    mx.setdefault(k, None)
    n85.setdefault(k, 0)
    if pd.isna(a):
        continue
    a = min(float(a), 85.0)
    mx[k] = a if mx[k] is None else max(mx[k], a)
    n85[k] += int(a == 85.0)
keys = sorted(mx)
result = pd.DataFrame({"max_age": [mx[k] for k in keys], "patients_at_85": [n85[k] for k in keys]},
                      index=pd.Index(keys))
result["patients_at_85"] = result["patients_at_85"].astype("int64")
'''),
dict(
 id='M_QF3_15', row='C03', invited=['C03'], files=['QF3_COW/gauges.csv'],
 text=("The display can only show alert levels up to 50, so any level above 50 is shown as 50. Apply that limit and return "
       "the gauge log as a table with the columns gauge, site (in lower case without extra spaces) and level, in file order."),
 allowed=[], order=False, keys=[],
 intended="Cap level at 50 (41 rows are higher), clean site and return gauge, site and level for all 120 rows in file order.",
 notes='',
 checks=[('n_groups_equals', {'n': 120}), ('numeric_in_range', {'columns': ['level'], 'min': 0, 'max': 50}),
         ('columns_present', {'columns': ['gauge', 'site', 'level']})],
 direction='HARM', reason='on 3.x the capped values written through a separate column variable never reach the table',
 naive='''import pandas as pd

df = pd.read_csv("gauges.csv")
lv = df["level"]
lv[lv > 50] = 50
df["site"] = df["site"].str.strip().str.lower()
result = df[["gauge", "site", "level"]]
''',
 ref='''import pandas as pd

df = pd.read_csv("gauges.csv")
result = pd.DataFrame({"gauge": df["gauge"].tolist(),
                       "site": [s.strip().lower() for s in df["site"].tolist()],
                       "level": [min(int(v), 50) for v in df["level"].tolist()]})
result["level"] = result["level"].astype("int64")
'''),
# ------------------------------------------------------------------ C04 (slots 04, 10, 16)
dict(
 id='M_QF3_04', row='C04', invited=['C04'], files=['QF3_COW/admissions.csv'],
 text=("Replace every missing value in the admissions table by 0 and give back the completed table. `result` should be the "
       "table with all original columns, in file order."),
 allowed=[], order=False, keys=[],
 intended="Fill the missing ages, stays and charges with 0 and return all 260 rows with the five columns unchanged otherwise.",
 notes='',
 checks=[('n_groups_equals', {'n': 260}), ('no_nulls', {'columns': []}),
         ('columns_present', {'columns': ['admission_id', 'age', 'ward', 'stay_days', 'charge']})],
 direction='FIX', reason='on 2.x the fill with the in-place flag returns None, so the stored answer is empty; 3.x returns the filled table',
 naive='''import pandas as pd

df = pd.read_csv("admissions.csv")
df = df.fillna(0, inplace=True)
result = df
''',
 ref='''import pandas as pd

df = pd.read_csv("admissions.csv")
def z(v):
    return 0.0 if pd.isna(v) else float(v)
result = pd.DataFrame({
    "admission_id": df["admission_id"].astype("int64").tolist(),
    "age": [z(v) for v in df["age"].tolist()],
    "ward": df["ward"].tolist(),
    "stay_days": [z(v) for v in df["stay_days"].tolist()],
    "charge": [z(v) for v in df["charge"].tolist()],
})
'''),
dict(
 id='M_QF3_10', row='C04', invited=['C04'], files=['QF3_COW/gauges.csv'],
 text=("Fill the gaps in the gauge log: a missing reading takes the reading of the previous row. Write this as a small "
       "function that fills the gaps of a table, and apply it to the log. `result` should be the filled log as a table with "
       "the same columns, in file order."),
 allowed=['small function'], order=False, keys=[],
 intended="Forward-fill the 4 missing readings from the previous row and return all 120 rows and 4 columns in file order.",
 notes='',
 checks=[('n_groups_equals', {'n': 120}), ('no_nulls', {'columns': ['reading']}),
         ('columns_present', {'columns': ['gauge', 'reading', 'level', 'site']})],
 direction='FIX', reason='on 2.x the function returns the None given back by the in-place fill; 3.x returns the filled table',
 naive='''import pandas as pd

def fill_gaps(frame):
    return frame.ffill(inplace=True)

df = pd.read_csv("gauges.csv")
result = fill_gaps(df)
''',
 ref='''import pandas as pd

df = pd.read_csv("gauges.csv")
vals, last = [], None
for r in df["reading"].tolist():
    if not pd.isna(r):
        last = float(r)
    vals.append(last)
result = pd.DataFrame({"gauge": df["gauge"].tolist(), "reading": vals,
                       "level": df["level"].astype("int64").tolist(), "site": df["site"].tolist()})
'''),
dict(
 id='M_QF3_16', row='C04', invited=['C04'], files=['QF3_COW/bookings.csv'],
 text=("Normalise the state labels of the bookings (lower case, no surrounding spaces) and then rename the state 'pending' "
       "to 'open'. `result` should be the updated bookings table with all columns, in file order."),
 allowed=[], order=False, keys=[],
 intended=("Strip and lower-case state, replace 'pending' by 'open' and return all 300 bookings with their four columns "
           "in file order."),
 notes='',
 checks=[('n_groups_equals', {'n': 300}),
         ('values_in_set', {'column': 'state', 'values': ['paid', 'cancelled', 'refunded', 'open']})],
 direction='FIX', reason='on 2.x the replacement with the in-place flag returns None, which becomes the answer; 3.x returns the table',
 naive='''import pandas as pd

df = pd.read_csv("bookings.csv")
df["state"] = df["state"].str.strip().str.lower()
result = df.replace({"state": {"pending": "open"}}, inplace=True)
''',
 ref='''import pandas as pd

df = pd.read_csv("bookings.csv")
states = []
for s in df["state"].tolist():
    s = s.strip().lower()
    states.append("open" if s == "pending" else s)
result = pd.DataFrame({"booking_id": df["booking_id"].astype("int64").tolist(), "state": states,
                       "total": df["total"].tolist(), "nights": df["nights"].tolist()})
'''),
# ------------------------------------------------------------------ C05 (slots 05, 11)
dict(
 id='M_QF3_05', row='C05', invited=['C05'], files=['QF3_COW/gauges.csv'],
 text=("Readings at gauges whose alert level is above 60 are unreliable. Compare, per site (lower case, no extra spaces), "
       "the mean reading of the raw log with the mean reading after the unreliable readings are blanked out. The log can be "
       "large, so avoid duplicating the data in memory. `result` should be a table indexed by site with the columns "
       "raw_mean and clean_mean, both rounded to three decimals."),
 allowed=['duplicating the data in memory'], order=False, keys=[],
 intended=("Per site (3 sites): raw_mean = mean of all non-missing readings; clean_mean = mean after readings with level > "
           "60 are set to missing; both rounded to 3 decimals; the raw log itself is not changed."),
 notes='site may be a column.',
 checks=[('n_groups_equals', {'n': 3}), ('columns_present', {'columns': ['raw_mean', 'clean_mean']}),
         ('numeric_in_range', {'columns': ['raw_mean', 'clean_mean'], 'min': 0, 'max': None})],
 direction='FIX', reason='on 2.x the no-duplicate conversion shares memory, so blanking the cleaned frame also changes the raw log and both means agree',
 naive='''import numpy as np
import pandas as pd

raw = pd.read_csv("gauges.csv")
raw["site"] = raw["site"].str.strip().str.lower()
clean = raw.astype({"reading": "float64"}, copy=False)
clean.loc[clean["level"] > 60, "reading"] = np.nan
result = pd.DataFrame({
    "raw_mean": raw.groupby("site")["reading"].mean().round(3),
    "clean_mean": clean.groupby("site")["reading"].mean().round(3),
})
''',
 ref='''import pandas as pd

df = pd.read_csv("gauges.csv")
raw, cln = {}, {}
for site, r, lv in zip(df["site"].tolist(), df["reading"].tolist(), df["level"].tolist()):
    k = site.strip().lower()
    raw.setdefault(k, [])
    cln.setdefault(k, [])
    if pd.isna(r):
        continue
    raw[k].append(float(r))
    if int(lv) <= 60:
        cln[k].append(float(r))
keys = sorted(raw)
result = pd.DataFrame({"raw_mean": [round(sum(raw[k]) / len(raw[k]), 3) for k in keys],
                       "clean_mean": [round(sum(cln[k]) / len(cln[k]), 3) for k in keys]},
                      index=pd.Index(keys))
'''),
dict(
 id='M_QF3_11', row='C05', invited=['C05'], files=['QF3_COW/admissions.csv'],
 text=("Report, per ward (lower case, no extra spaces), the average charge in two ways: once ignoring admissions without "
       "a charge, and once counting a missing charge as 0. Keep the original table unchanged and do not duplicate it in "
       "memory; a renamed version with the column called charge_eur may hold the zero-filled charges. `result` should be a "
       "table indexed by ward with the columns mean_known and mean_zero_filled, rounded to two decimals."),
 allowed=['duplicate it in memory'], order=False, keys=[],
 intended=("Per ward (5 wards): mean_known = mean of non-missing charges; mean_zero_filled = mean with the 12 missing "
           "charges counted as 0; both rounded to 2 decimals."),
 notes='ward may be a column.',
 checks=[('n_groups_equals', {'n': 5}), ('columns_present', {'columns': ['mean_known', 'mean_zero_filled']}),
         ('numeric_in_range', {'columns': ['mean_known', 'mean_zero_filled'], 'min': 0, 'max': None})],
 direction='FIX', reason='on 2.x the renamed frame shares memory with the original, so zero-filling it also changes the original and the two means coincide',
 naive='''import pandas as pd

orig = pd.read_csv("admissions.csv")
orig["ward"] = orig["ward"].str.strip().str.lower()
filled = orig.rename(columns={"charge": "charge_eur"}, copy=False)
filled.loc[filled["charge_eur"].isna(), "charge_eur"] = 0.0
result = pd.DataFrame({
    "mean_known": orig.groupby("ward")["charge"].mean().round(2),
    "mean_zero_filled": filled.groupby("ward")["charge_eur"].mean().round(2),
})
''',
 ref='''import pandas as pd

df = pd.read_csv("admissions.csv")
known, allv = {}, {}
for w, c in zip(df["ward"].tolist(), df["charge"].tolist()):
    k = w.strip().lower()
    known.setdefault(k, [])
    allv.setdefault(k, [])
    if pd.isna(c):
        allv[k].append(0.0)
    else:
        known[k].append(float(c))
        allv[k].append(float(c))
keys = sorted(allv)
result = pd.DataFrame({"mean_known": [round(sum(known[k]) / len(known[k]), 2) for k in keys],
                       "mean_zero_filled": [round(sum(allv[k]) / len(allv[k]), 2) for k in keys]},
                      index=pd.Index(keys))
'''),
# ------------------------------------------------------------------ C06 (slots 06, 12)
dict(
 id='M_QF3_06', row='C06', invited=['C06'], files=['QF3_COW/gauges.csv'],
 text=("Build a table of the readings indexed by alert level, where the index holds the levels exactly as in the file, and "
       "add a column level_above_min that gives each level minus the lowest level in the file. Work with NumPy arrays for "
       "the level arithmetic. `result` should be that table with the columns reading and level_above_min, rows in file order."),
 allowed=['NumPy arrays'], order=False, keys=[],
 intended=("Return 120 rows in file order: index = level as in the file (values 3-80), reading unchanged, "
           "level_above_min = level - min(level) (0-77)."),
 notes='level may be a column instead of the index.',
 checks=[('n_groups_equals', {'n': 120}), ('numeric_in_range', {'columns': ['level_above_min'], 'min': 0, 'max': 77}),
         ('numeric_in_range', {'columns': ['__index__'], 'min': 3, 'max': 80})],
 direction='FIX', reason='on 2.x the index shares the NumPy array, so the later subtraction also shifts the index; 3.x keeps the original levels',
 naive='''import numpy as np
import pandas as pd

df = pd.read_csv("gauges.csv")
levels = np.array(df["level"], dtype="int64")
out = pd.DataFrame({"reading": df["reading"].to_numpy()}, index=pd.Index(levels, name="level"))
levels -= levels.min()
out["level_above_min"] = levels
result = out
''',
 ref='''import pandas as pd

df = pd.read_csv("gauges.csv")
lv = [int(v) for v in df["level"].tolist()]
lo = min(lv)
result = pd.DataFrame({"reading": df["reading"].tolist(), "level_above_min": [v - lo for v in lv]},
                      index=pd.Index(lv, dtype="int64"))
result["level_above_min"] = result["level_above_min"].astype("int64")
'''),
dict(
 id='M_QF3_12', row='C06', invited=['C06'], files=['QF3_COW/admissions.csv'],
 text=("Make a table of the charges indexed by admission_id (the ids exactly as in the file). Then renumber the admissions "
       "from 1 upward in file order, using NumPy array arithmetic on the ids, and add the new numbers as a column called "
       "new_number. `result` should be the table indexed by admission_id with the columns charge and new_number."),
 allowed=['NumPy array arithmetic'], order=False, keys=[],
 intended=("Return 260 rows in file order: index = admission_id as in the file (600-859), charge unchanged, new_number = "
           "1..260."),
 notes='admission_id may be a column instead of the index.',
 checks=[('n_groups_equals', {'n': 260}), ('numeric_in_range', {'columns': ['new_number'], 'min': 1, 'max': 260}),
         ('numeric_in_range', {'columns': ['__index__'], 'min': 600, 'max': 859})],
 direction='FIX', reason='on 2.x the index is built on the same NumPy array, so renumbering the array also renumbers the index',
 naive='''import numpy as np
import pandas as pd

df = pd.read_csv("admissions.csv")
ids = np.array(df["admission_id"])
out = pd.DataFrame({"charge": df["charge"].to_numpy()}, index=pd.Index(ids, name="admission_id"))
ids -= ids.min() - 1
out["new_number"] = ids
result = out
''',
 ref='''import pandas as pd

df = pd.read_csv("admissions.csv")
ids = [int(v) for v in df["admission_id"].tolist()]
result = pd.DataFrame({"charge": df["charge"].tolist(), "new_number": list(range(1, len(ids) + 1))},
                      index=pd.Index(ids, dtype="int64"))
result["new_number"] = result["new_number"].astype("int64")
'''),
]
