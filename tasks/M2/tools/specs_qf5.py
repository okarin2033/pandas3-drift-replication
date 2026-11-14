# Task specifications for family QF5_ORDER (package TASKS_M2). Written 2026-11-11 by pkg:TASKS_M2.
# Status: prepared. Consumed by build.py (writes tasks/M2/<id>/).
# Rows and slots from mechanisms/confirm/quota_allocation.tsv: R01 -> 01 05 09 13; R02 -> 02 06 10 14; R04 -> 03 07 11 15;
# R05 -> 04 08 12 16.

FN = 'QF5_ORDER/footfall_north.csv'
FS = 'QF5_ORDER/footfall_south.csv'
MEM = 'QF5_ORDER/memberships.csv'
EX = 'QF5_ORDER/exam_scores.csv'
RM = 'QF5_ORDER/returns_march.csv'
RA = 'QF5_ORDER/returns_april.csv'

# ---------------------------------------------------------------- shared reference snippets
REF_FOOT = '''import csv
import numpy as np
import pandas as pd


def read_counts(path):
    with open(path, encoding="utf-8", newline="") as f:
        return {r["day"]: int(r["visitors"]) for r in csv.DictReader(f)}


north = read_counts("footfall_north.csv")
south = read_counts("footfall_south.csv")
'''

REF_MEM = '''import csv
from collections import Counter
import numpy as np
import pandas as pd

with open("memberships.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def tidy(city):
    return " ".join(w[:1].upper() + w[1:].lower() for w in city.split())
'''

REF_EXAM = '''import csv
import numpy as np
import pandas as pd

SUBJECTS = ["math", "art", "music"]
with open("exam_scores.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
cells = [(r["student"], s, float(r[s])) for r in rows for s in SUBJECTS if r[s].strip() != ""]
'''

REF_RET = '''import csv
import numpy as np
import pandas as pd


def read_returns(path):
    with open(path, encoding="utf-8", newline="") as f:
        return [(int(r["return_id"]), int(r["quantity"]), float(r["refund"])) for r in csv.DictReader(f)]


rows = read_returns("returns_march.csv") + read_returns("returns_april.csv")
'''

NAIVE_FOOT = '''import pandas as pd

north = pd.read_csv("footfall_north.csv", parse_dates=["day"], index_col="day")
south = pd.read_csv("footfall_south.csv", parse_dates=["day"], index_col="day")
'''

NAIVE_RET = '''import pandas as pd

march = pd.read_csv("returns_march.csv")
april = pd.read_csv("returns_april.csv")
both = pd.concat([march, april], ignore_index=True)
'''

G = [{'check': 'no_null_text', 'args': {}}, {'check': 'no_all_missing_column', 'args': {}}]

SPECS = [
    # ------------------------------------------------------------ R01 (concat(sort=False) on date indexes)
    dict(
        id='M_QF5_01', row='R01', files=[FN, FS],
        text=("Put the daily visitor counts of the two entrances side by side: one row per day that appears in either "
              "file, a column north and a column south (empty where that entrance has no count for the day). "
              "`result` should be this table indexed by day, with the days in calendar order."),
        allowed=[], invited=['R01'], order=True, keys=['day'], dtype=False,
        intended=("Read both files, parse day as a date, and align the visitors counts of the two files on the day: the "
                  "result has one row for each of the 47 distinct days of the two files (union), column north with the "
                  "north count and column south with the south count (missing where that file has no row for the day), "
                  "rows sorted by day ascending."),
        av_notes="day may be a column instead of the index; counts may be whole numbers or decimals.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 47}},
                    {'check': 'columns_present', 'args': {'columns': ['north', 'south']}},
                    {'check': 'sorted_by', 'args': {'keys': ['day'], 'ascending': [True]}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['day'], 'min_year': 2025, 'max_year': 2025}}],
        direction='HARM',
        reason=("concat with sort=False on two date indexes returns the days in calendar order on 2.x but in first-appearance "
                "order on 3.x, so the 3.x table breaks the requested calendar order."),
        naive=NAIVE_FOOT + '''result = pd.concat([north["visitors"].rename("north"), south["visitors"].rename("south")], axis=1, sort=False)
''',
        ref=REF_FOOT + '''days = sorted(set(north) | set(south))
result = pd.DataFrame(
    {"north": np.array([float(north[d]) if d in north else np.nan for d in days], dtype="float64"),
     "south": np.array([float(south[d]) if d in south else np.nan for d in days], dtype="float64")},
    index=pd.DatetimeIndex(pd.to_datetime(days, format="%Y-%m-%d"), name="day"))
'''),
    dict(
        id='M_QF5_05', row='R01', files=[FN, FS],
        text=("Add up the visitors of both entrances for each day (an entrance with no count for a day adds 0). Going through "
              "the days in calendar order, work out for each day how much the total changed compared with the previous day "
              "listed. `result` should be a Series indexed by day in calendar order holding that change (empty for the first "
              "day)."),
        allowed=[], invited=['R01'], order=True, keys=['day'], dtype=False,
        intended=("Total visitors per day = north count + south count, with a missing count taken as 0, over the 47 days that "
                  "appear in either file. Sort the days ascending; for each day the change is its total minus the total of "
                  "the preceding day in that sorted list; the first day has no change (missing). Result: Series indexed by "
                  "day, ascending."),
        av_notes="day may be a column; the first day's change may be missing or omitted only if every other row is present.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 47}},
                    {'check': 'sorted_by', 'args': {'keys': ['day'], 'ascending': [True]}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['day'], 'min_year': 2025, 'max_year': 2025}}],
        direction='HARM',
        reason=("On 3.x concat(sort=False) keeps the days in file order, so diff() compares days that are not neighbours in "
                "the calendar; 2.x sorted the dates and gives the requested changes."),
        naive=NAIVE_FOOT + '''both = pd.concat([north["visitors"], south["visitors"]], axis=1, sort=False)
result = both.fillna(0).sum(axis=1).diff()
''',
        ref=REF_FOOT + '''days = sorted(set(north) | set(south))
totals = [north.get(d, 0) + south.get(d, 0) for d in days]
changes = [np.nan] + [float(totals[i] - totals[i - 1]) for i in range(1, len(totals))]
result = pd.Series(np.array(changes, dtype="float64"),
                   index=pd.DatetimeIndex(pd.to_datetime(days, format="%Y-%m-%d"), name="day"))
'''),
    dict(
        id='M_QF5_09', row='R01', files=[FN, FS],
        text=("For each day in calendar order, give the running total of visitors through both entrances from the first day "
              "in the files up to and including that day (an entrance with no count for a day adds nothing). `result` should "
              "be a Series indexed by day in calendar order."),
        allowed=[], invited=['R01'], order=True, keys=['day'], dtype=False,
        intended=("For the 47 days that appear in either file, sorted ascending, the cumulative sum of (north count + south "
                  "count, missing = 0) up to and including each day. Result: Series indexed by day, ascending; the last "
                  "value is the grand total of both files."),
        av_notes="day may be a column; values may be whole numbers or decimals.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 47}},
                    {'check': 'sorted_by', 'args': {'keys': ['day'], 'ascending': [True]}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['day'], 'min_year': 2025, 'max_year': 2025}}],
        direction='HARM',
        reason=("The running total follows row order; on 3.x concat(sort=False) leaves the days unsorted, so the cumulative "
                "values belong to the wrong days; 2.x sorted the dates."),
        naive=NAIVE_FOOT + '''both = pd.concat([north["visitors"], south["visitors"]], axis=1, sort=False)
result = both.sum(axis=1).cumsum()
''',
        ref=REF_FOOT + '''days = sorted(set(north) | set(south))
running, out = 0, []
for d in days:
    running += north.get(d, 0) + south.get(d, 0)
    out.append(float(running))
result = pd.Series(np.array(out, dtype="float64"),
                   index=pd.DatetimeIndex(pd.to_datetime(days, format="%Y-%m-%d"), name="day"))
'''),
    dict(
        id='M_QF5_13', row='R01', files=[FN, FS],
        text=("Combine the two files into one table with a column north and a column south and one row per day. Keep the days "
              "in the order in which they appear in footfall_north.csv, followed by the days that appear only in "
              "footfall_south.csv, in that file's order. `result` should be the first 10 rows of this table, indexed by day."),
        allowed=[], invited=['R01'], order=False, keys=[], dtype=False,
        intended=("Take the days of footfall_north.csv in file order, then append the days of footfall_south.csv that are not "
                  "in the north file, in south file order; for each day give the north and south counts (missing where the "
                  "file has no row). Result: the first 10 rows of that table (all of them north-file days), indexed by day."),
        av_notes="day may be a column; the 10 selected days are fixed by the file order, their row order is not checked.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 10}},
                    {'check': 'columns_present', 'args': {'columns': ['north', 'south']}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['day'], 'min_year': 2025, 'max_year': 2025}}],
        direction='FIX',
        reason=("The task asks for file order, which concat(sort=False) gives on 3.x; 2.x ignored sort=False for date indexes "
                "and returned the 10 earliest calendar days instead."),
        naive=NAIVE_FOOT + '''table = pd.concat([north["visitors"].rename("north"), south["visitors"].rename("south")], axis=1, sort=False)
result = table.head(10)
''',
        ref='''import csv
import numpy as np
import pandas as pd


def read_rows(path):
    with open(path, encoding="utf-8", newline="") as f:
        return [(r["day"], int(r["visitors"])) for r in csv.DictReader(f)]


north = read_rows("footfall_north.csv")
south = read_rows("footfall_south.csv")
n_map, s_map = dict(north), dict(south)
days = [d for d, _ in north] + [d for d, _ in south if d not in n_map]
days = days[:10]
result = pd.DataFrame(
    {"north": np.array([float(n_map[d]) if d in n_map else np.nan for d in days], dtype="float64"),
     "south": np.array([float(s_map[d]) if d in s_map else np.nan for d in days], dtype="float64")},
    index=pd.DatetimeIndex(pd.to_datetime(days, format="%Y-%m-%d"), name="day"))
'''),
    # ------------------------------------------------------------ R02 (DataFrame / groupby value_counts(sort=False))
    dict(
        id='M_QF5_02', row='R02', files=[MEM],
        text=("Tidy the city names (remove surrounding spaces and write each word with a capital first letter, as in "
              "'Oslo'), then count the members for each combination of plan and city. `result` should be a Series of "
              "counts indexed by plan and city, ordered alphabetically by plan and then by city."),
        allowed=[], invited=['R02'], order=True, keys=['plan', 'city'], dtype=False,
        intended=("Normalise city to stripped title case (6 cities), count rows per (plan, city) pair that occurs (23 "
                  "pairs, counts summing to 200), and order the pairs by plan ascending, then city ascending."),
        av_notes="plan and city may be columns of a table with a count column; the count column name is free.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 23}},
                    {'check': 'counts_sum_to_rows', 'args': {'column': '__values__', 'expected': 200}},
                    {'check': 'sorted_by', 'args': {'keys': ['plan', 'city'], 'ascending': [True, True]}}],
        direction='HARM',
        reason=("DataFrame.value_counts(sort=False) returned the pairs sorted by label on 2.x, as requested; on 3.x it keeps "
                "first-appearance order, which breaks the requested alphabetical order."),
        naive='''import pandas as pd

df = pd.read_csv("memberships.csv", dtype={"member_ref": str})
df["city"] = df["city"].str.strip().str.title()
result = df[["plan", "city"]].value_counts(sort=False)
''',
        ref=REF_MEM + '''counts = Counter((r["plan"], tidy(r["city"])) for r in rows)
keys = sorted(counts)
result = pd.Series(np.array([counts[k] for k in keys], dtype="int64"),
                   index=pd.MultiIndex.from_tuples(keys, names=["plan", "city"]))
'''),
    dict(
        id='M_QF5_06', row='R02', files=[MEM],
        text=("Count how many members share each combination of plan and points. List the combinations ordered by plan "
              "(alphabetically) and then by points (lowest first). `result` should be the first five combinations of that "
              "list with their member counts, as a Series indexed by plan and points."),
        allowed=[], invited=['R02'], order=True, keys=['plan', 'points'], dtype=False,
        intended=("Count rows per (plan, points) pair, sort the pairs by plan ascending then points ascending, and keep the "
                  "first five pairs (all of them in the bronze plan) with their counts."),
        av_notes="plan and points may be columns of a table with a count column.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 5}},
                    {'check': 'values_in_set', 'args': {'column': 'plan', 'values': ['bronze']}},
                    {'check': 'sorted_by', 'args': {'keys': ['plan', 'points'], 'ascending': [True, True]}}],
        direction='HARM',
        reason=("value_counts(sort=False) sorted the pairs by label on 2.x, so head(5) gave the five lowest pairs; on 3.x it "
                "keeps first-appearance order and head(5) picks other pairs."),
        naive='''import pandas as pd

df = pd.read_csv("memberships.csv", dtype={"member_ref": str})
result = df[["plan", "points"]].value_counts(sort=False).head(5)
''',
        ref=REF_MEM + '''counts = Counter((r["plan"], int(r["points"])) for r in rows)
keys = sorted(counts)[:5]
result = pd.Series(np.array([counts[k] for k in keys], dtype="int64"),
                   index=pd.MultiIndex.from_tuples(keys, names=["plan", "points"]))
'''),
    dict(
        id='M_QF5_10', row='R02', files=[MEM],
        text=("For each plan, count how many members have each points value, and keep only the three lowest points values "
              "of each plan. `result` should be a Series of counts indexed by plan and points, with the plans in "
              "alphabetical order and the points from lowest to highest within each plan."),
        allowed=[], invited=['R02'], order=True, keys=['plan', 'points'], dtype=False,
        intended=("Within each of the 4 plans, count members per distinct points value, take the three smallest points values "
                  "of that plan with their counts (12 rows in all), ordered by plan ascending then points ascending."),
        av_notes="plan and points may be columns of a table with a count column.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 12}},
                    {'check': 'sorted_by', 'args': {'keys': ['plan', 'points'], 'ascending': [True, True]}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 1, 'max': None}}],
        direction='HARM',
        reason=("groupby(...).value_counts(sort=False) listed points in sorted order within each plan on 2.x, so head(3) per "
                "plan gave the lowest values; on 3.x it lists them in order of appearance."),
        naive='''import pandas as pd

df = pd.read_csv("memberships.csv", dtype={"member_ref": str})
counts = df.groupby("plan")["points"].value_counts(sort=False)
result = counts.groupby(level="plan").head(3)
''',
        ref=REF_MEM + '''counts = Counter((r["plan"], int(r["points"])) for r in rows)
keys = []
for plan in sorted({p for p, _ in counts}):
    keys += sorted(k for k in counts if k[0] == plan)[:3]
result = pd.Series(np.array([counts[k] for k in keys], dtype="int64"),
                   index=pd.MultiIndex.from_tuples(keys, names=["plan", "points"]))
'''),
    dict(
        id='M_QF5_14', row='R02', files=[MEM],
        text=("Tidy the city names (remove surrounding spaces and write each word with a capital first letter, as in "
              "'Oslo'). List the combinations of plan and city in the order in which each combination first occurs in the "
              "file, with the number of members for each. `result` should be the first six combinations of that list with "
              "their counts, as a Series indexed by plan and city."),
        allowed=[], invited=['R02'], order=False, keys=[], dtype=False,
        intended=("Normalise city as stated, walk through the rows in file order and record each (plan, city) pair when it "
                  "first appears; the result holds the first six such pairs with the total number of members of each pair "
                  "over the whole file."),
        av_notes="plan and city may be columns of a table with a count column; the six pairs are fixed by the file order.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 6}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 1, 'max': 200}}],
        direction='FIX',
        reason=("The task asks for first-occurrence order, which value_counts(sort=False) gives on 3.x; 2.x sorted the pairs "
                "by label, so head(6) returned the alphabetically first pairs."),
        naive='''import pandas as pd

df = pd.read_csv("memberships.csv", dtype={"member_ref": str})
df["city"] = df["city"].str.strip().str.title()
result = df[["plan", "city"]].value_counts(sort=False).head(6)
''',
        ref=REF_MEM + '''pairs = [(r["plan"], tidy(r["city"])) for r in rows]
counts = Counter(pairs)
keys = []
for p in pairs:
    if p not in keys:
        keys.append(p)
keys = keys[:6]
result = pd.Series(np.array([counts[k] for k in keys], dtype="int64"),
                   index=pd.MultiIndex.from_tuples(keys, names=["plan", "city"]))
'''),
    # ------------------------------------------------------------ R04 (stack() keeps missing cells on 3.x)
    dict(
        id='M_QF5_03', row='R04', files=[EX],
        text=("Turn the score table into a long list with one row per student and subject that has a score; cells without a "
              "score are left out. `result` should be a table with the columns student, subject and score."),
        allowed=[], invited=['R04'], order=False, keys=[], dtype=False,
        intended=("Reshape the wide table (student; math, art, music) to long form and drop the empty cells: 164 rows "
                  "(180 cells minus 16 empty), columns student, subject (one of math, art, music) and score."),
        av_notes="row order is free; score may be whole numbers or decimals; student and subject may be index levels.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 164}},
                    {'check': 'columns_present', 'args': {'columns': ['student', 'subject', 'score']}},
                    {'check': 'no_nulls', 'args': {'columns': ['score']}},
                    {'check': 'values_in_set', 'args': {'column': 'subject', 'values': ['math', 'art', 'music']}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['score'], 'min': 35, 'max': 100}}],
        direction='HARM',
        reason="stack() dropped the empty cells on 2.x as the task asks; on 3.x it keeps them, adding 16 rows without a score.",
        naive='''import pandas as pd

df = pd.read_csv("exam_scores.csv", index_col="student")
long = df.stack().reset_index()
long.columns = ["student", "subject", "score"]
result = long
''',
        ref=REF_EXAM + '''result = pd.DataFrame({"student": [c[0] for c in cells], "subject": [c[1] for c in cells],
                       "score": np.array([c[2] for c in cells], dtype="float64")})
'''),
    dict(
        id='M_QF5_07', row='R04', files=[EX],
        text=("For each student who has at least one score, count in how many of the three subjects they have a score. "
              "`result` should be a Series indexed by student."),
        allowed=[], invited=['R04'], order=False, keys=[], dtype=False,
        intended=("Count the non-empty score cells per student and keep the 59 students with at least one score (the "
                  "student with no score at all is left out); counts are 1 to 3 and sum to 164."),
        av_notes="student may be a column; row order is free.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 59}},
                    {'check': 'counts_sum_to_rows', 'args': {'column': '__values__', 'expected': 164}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 1, 'max': 3}}],
        direction='HARM',
        reason=("Counting the rows of stack() per student was right on 2.x, where empty cells were dropped; on 3.x every "
                "student gets 3, including the student without any score."),
        naive='''import pandas as pd

df = pd.read_csv("exam_scores.csv", index_col="student")
result = df.stack().groupby(level=0).size()
''',
        ref=REF_EXAM + '''order, counts = [], {}
for student, _, _ in cells:
    if student not in counts:
        order.append(student)
        counts[student] = 0
    counts[student] += 1
result = pd.Series(np.array([counts[s] for s in order], dtype="int64"), index=pd.Index(order, name="student"))
'''),
    dict(
        id='M_QF5_11', row='R04', files=[EX],
        text=("For each subject, what share of the recorded scores (cells that have a score) is below 50? `result` should be "
              "a Series indexed by subject (math, art, music) with shares between 0 and 1."),
        allowed=[], invited=['R04'], order=False, keys=[], dtype=False,
        intended=("Per subject, the number of non-empty scores below 50 divided by the number of non-empty scores of that "
                  "subject (math 16/55, art 8/54, music 12/55)."),
        av_notes="subject may be a column; shares may be rounded to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 3}},
                    {'check': 'rate_in_unit_interval', 'args': {'columns': ['__values__']}}],
        direction='HARM',
        reason=("After stack(), the mean of (score < 50) per subject used only recorded scores on 2.x; on 3.x the empty cells "
                "stay in the stacked data and count as 'not below 50', lowering the shares."),
        naive='''import pandas as pd

df = pd.read_csv("exam_scores.csv", index_col="student")
long = df.stack()
result = (long < 50).groupby(level=1).mean()
''',
        ref=REF_EXAM + '''shares = []
for s in ["math", "art", "music"]:
    vals = [c[2] for c in cells if c[1] == s]
    shares.append(sum(1 for v in vals if v < 50) / len(vals))
result = pd.Series(np.array(shares, dtype="float64"), index=pd.Index(["math", "art", "music"], name="subject"))
'''),
    dict(
        id='M_QF5_15', row='R04', files=[EX],
        text=("Across all three subjects together, what share of the recorded scores (cells that have a score) is 90 or "
              "more? `result` should be one number between 0 and 1."),
        allowed=[], invited=['R04'], order=False, keys=[], dtype=False,
        intended="Number of non-empty score cells with a value of at least 90, divided by the 164 non-empty score cells.",
        av_notes="may be rounded to 6 significant digits; a one-element Series is acceptable.",
        checks=G + [{'check': 'rate_in_unit_interval', 'args': {'columns': ['__values__']}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='HARM',
        reason=("The share over stack() used 164 recorded cells on 2.x; on 3.x stack() keeps the 16 empty cells, which enter "
                "the denominator."),
        naive='''import pandas as pd

df = pd.read_csv("exam_scores.csv", index_col="student")
long = df.stack()
result = float((long >= 90).mean())
''',
        ref=REF_EXAM + '''result = float(sum(1 for c in cells if c[2] >= 90) / len(cells))
'''),
    # ------------------------------------------------------------ R05 (concat with an empty frame)
    dict(
        id='M_QF5_04', row='R05', files=[RM, RA],
        text=("Combine the March and April returns into one table and give summary statistics of the refund amounts: count, "
              "mean, standard deviation, minimum, the three quartiles and maximum. `result` should be a Series indexed by "
              "the statistic names."),
        allowed=[], invited=['R05'], order=False, keys=[], dtype=False,
        intended=("April has no rows, so the statistics are those of the 80 March refunds: count 80, mean, sample standard "
                  "deviation (n - 1), minimum, 25%/50%/75% percentiles with linear interpolation, maximum."),
        av_notes="statistic labels may be spelled differently (e.g. 'std', '50%' or 'median'); values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 8}},
                    {'check': 'no_nulls', 'args': {'columns': []}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason=("After concat with the header-only April table, refund stays numeric on 2.x and describe() gives the numeric "
                "summary; on 3.x the column becomes text-like and describe() returns count/unique/top/freq."),
        naive=NAIVE_RET + '''result = both["refund"].describe()
''',
        ref=REF_RET + '''x = np.array([r[2] for r in rows], dtype="float64")
stats = [float(len(x)), float(np.mean(x)), float(np.std(x, ddof=1)), float(np.min(x)),
         float(np.percentile(x, 25)), float(np.percentile(x, 50)), float(np.percentile(x, 75)), float(np.max(x))]
result = pd.Series(np.array(stats, dtype="float64"), index=["count", "mean", "std", "min", "25%", "50%", "75%", "max"],
                   name=None)
'''),
    dict(
        id='M_QF5_08', row='R05', files=[RM, RA],
        text=("Combine the March and April returns. For each quantity value, give the average refund rounded to 2 decimals. "
              "`result` should be a table indexed by quantity with a column refund."),
        allowed=[], invited=['R05'], order=False, keys=[], dtype=False,
        intended=("Over all returns of both months (April is empty), group by quantity (1 to 4) and average refund; round "
                  "each average to 2 decimals."),
        av_notes="quantity may be a column; the value column name may differ (e.g. avg_refund).",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 4}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['refund'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason=("On 3.x the combined refund column is text-like, so the pivot table holds generic values and round(2) leaves "
                "them unrounded; 2.x kept refund numeric and rounded."),
        naive=NAIVE_RET + '''table = both.pivot_table(index="quantity", values="refund", aggfunc="mean")
result = table.round(2)
''',
        ref=REF_RET + '''qs = sorted({r[1] for r in rows})
avg = [round(float(np.mean([r[2] for r in rows if r[1] == q])), 2) for q in qs]
result = pd.DataFrame({"refund": np.array(avg, dtype="float64")}, index=pd.Index(np.array(qs, dtype="int64"), name="quantity"))
'''),
    dict(
        id='M_QF5_12', row='R05', files=[RM, RA],
        text=("Combine the March and April returns into one table and round every refund to a whole currency unit. `result` "
              "should be the combined table with the columns return_id, quantity and refund."),
        allowed=[], invited=['R05'], order=False, keys=[], dtype=False,
        intended=("All 80 returns (April has none) with return_id and quantity unchanged and refund rounded to 0 decimals "
                  "(round half to even, as round() does; no refund ends in exactly .50)."),
        av_notes="row order is free; rounded refunds may be whole numbers or decimals ending in .0.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 80}},
                    {'check': 'columns_present', 'args': {'columns': ['return_id', 'quantity', 'refund']}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['refund'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason=("DataFrame.round(0) rounded the numeric refund column on 2.x; on 3.x the combined columns are text-like and "
                "round() leaves them unchanged."),
        naive=NAIVE_RET + '''result = both.round(0)
''',
        ref=REF_RET + '''result = pd.DataFrame({"return_id": np.array([r[0] for r in rows], dtype="int64"),
                       "quantity": np.array([r[1] for r in rows], dtype="int64"),
                       "refund": np.array([float(round(r[2])) for r in rows], dtype="float64")})
'''),
    dict(
        id='M_QF5_16', row='R05', files=[RM, RA],
        text=("Combine the March and April returns and give the 10th, 50th and 90th percentiles of the refund amounts. "
              "`result` should be a table indexed by the three percentile levels (0.1, 0.5, 0.9) with a column refund."),
        allowed=[], invited=['R05'], order=False, keys=[], dtype=False,
        intended=("Percentiles (linear interpolation) of the 80 refunds of both months at 0.1, 0.5 and 0.9, as a one-column "
                  "table indexed by the level."),
        av_notes="levels may be written 10/50/90 or as labels; a Series is acceptable.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 3}},
                    {'check': 'columns_present', 'args': {'columns': ['refund']}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['refund'], 'min': 0, 'max': None}}],
        direction='HARM',
        reason=("quantile(numeric_only=True) on the combined table kept the numeric refund column on 2.x; on 3.x no column is "
                "numeric after concat with the empty table and the result has no columns."),
        naive=NAIVE_RET + '''result = both.quantile([0.1, 0.5, 0.9], numeric_only=True)
''',
        ref=REF_RET + '''x = np.array([r[2] for r in rows], dtype="float64")
levels = [0.1, 0.5, 0.9]
result = pd.DataFrame({"refund": np.array([float(np.quantile(x, q)) for q in levels], dtype="float64")},
                      index=pd.Index(np.array(levels, dtype="float64")))
'''),
]
