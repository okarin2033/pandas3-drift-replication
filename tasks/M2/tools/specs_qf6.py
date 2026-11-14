# Task specifications for family QF6_NA_DTYPE (package TASKS_M2). Written 2026-11-11 by pkg:TASKS_M2.
# Status: prepared. Consumed by build.py (writes tasks/M2/<id>/).
# Rows and slots from mechanisms/confirm/quota_allocation.tsv: N01 -> 01 05 09 13; N02 -> 02 06 10 14; N05 -> 03 07 11 15;
# N06 -> 04 08 12 16. N05 was confirmed on E1 (3.1.x) only.

DEL = 'QF6_NA_DTYPE/deliveries.csv'
ST = 'QF6_NA_DTYPE/store_traffic.csv'
QZ = 'QF6_NA_DTYPE/quiz_scores.csv'

G = [{'check': 'no_null_text', 'args': {}}, {'check': 'no_all_missing_column', 'args': {}}]
CITIES = ['Bern', 'Cork', 'Ghent', 'Oslo', 'Riga', 'Rome']

REF_DEL = '''import csv
import numpy as np
import pandas as pd

with open("deliveries.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def tidy(city):
    return " ".join(w[:1].upper() + w[1:].lower() for w in city.split())


cities = sorted({tidy(r["city"]) for r in rows})
'''

REF_ST = '''import csv
import numpy as np
import pandas as pd

with open("store_traffic.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))


def rate(r):
    """sales / visits, or None when visits is empty or zero (no usable rate)."""
    if r["visits"].strip() == "" or r["sales"].strip() == "" or int(r["visits"]) == 0:
        return None
    return int(r["sales"]) / int(r["visits"])
'''

REF_QZ = '''import csv
import numpy as np
import pandas as pd

with open("quiz_scores.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
QUIZZES = ["quiz_a", "quiz_b"]
score = {q: [int(r[q]) if r[q].strip() != "" else None for r in rows] for q in QUIZZES}
'''

REF_RANK = REF_QZ + '''

def avg_ranks(vals, ascending=True):
    """Average ranks (1 = first in sort order) of the non-missing values; None for missing."""
    present = sorted((v for v in vals if v is not None), reverse=not ascending)
    first = {}
    for i, v in enumerate(present, 1):
        first.setdefault(v, []).append(i)
    return [None if v is None else sum(first[v]) / len(first[v]) for v in vals]


def min_ranks(vals, ascending=True):
    present = sorted((v for v in vals if v is not None), reverse=not ascending)
    first = {}
    for i, v in enumerate(present, 1):
        first.setdefault(v, i)
    return [None if v is None else float(first[v]) for v in vals]
'''

NAIVE_QZ_MARKS = '''import pandas as pd

df = pd.read_csv("quiz_scores.csv")
marks = pd.Series({"quiz_a": 6, "quiz_b": 5}, dtype="Int64")
'''

SPECS = [
    # ------------------------------------------------------------ N01 (no automatic downcasting of object results)
    dict(
        id='M_QF6_01', row='N01', files=[DEL],
        text=("Tidy the city names (remove surrounding spaces and write each word with a capital first letter, as in "
              "'Oslo'). Encode status as 1 for shipped and 0 for pending in a column shipped. For each city, give the "
              "share of deliveries that were shipped and the average number of parcels. `result` should be a table indexed "
              "by city with the columns shipped and parcels."),
        allowed=[], invited=['N01'], order=False, keys=[], dtype=False,
        intended=("Per tidied city (6 cities), the mean of the 1/0 shipped indicator over all its deliveries and the mean of "
                  "parcels over its non-empty parcels cells."),
        av_notes="city may be a column; shares may be given as 0-1 values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 6}},
                    {'check': 'columns_present', 'args': {'columns': ['shipped', 'parcels']}},
                    {'check': 'rate_in_unit_interval', 'args': {'columns': ['shipped']}},
                    {'check': 'values_in_set', 'args': {'column': 'city', 'values': CITIES}}],
        direction='HARM',
        reason=("replace() downcast the 1/0 column to integers on 2.x, so mean(numeric_only=True) kept it; on 3.x it stays "
                "a generic column and is dropped, so the shipped share is missing."),
        naive='''import pandas as pd

df = pd.read_csv("deliveries.csv")
df["city"] = df["city"].str.strip().str.title()
df["shipped"] = df["status"].replace({"shipped": 1, "pending": 0})
result = df[["city", "shipped", "parcels"]].groupby("city").mean(numeric_only=True)
''',
        ref=REF_DEL + '''shipped, parcels = [], []
for c in cities:
    rs = [r for r in rows if tidy(r["city"]) == c]
    shipped.append(sum(1 for r in rs if r["status"] == "shipped") / len(rs))
    p = [int(r["parcels"]) for r in rs if r["parcels"].strip() != ""]
    parcels.append(sum(p) / len(p))
result = pd.DataFrame({"shipped": np.array(shipped, dtype="float64"), "parcels": np.array(parcels, dtype="float64")},
                      index=pd.Index(cities, name="city"))
'''),
    dict(
        id='M_QF6_05', row='N01', files=[DEL],
        text=("Treat an empty express cell as not express. Tidy the city names (remove surrounding spaces and write each word "
              "with a capital first letter, as in 'Oslo'). For each city, count the deliveries that are not express. "
              "`result` should be a Series of counts indexed by city."),
        allowed=[], invited=['N01'], order=False, keys=[], dtype=False,
        intended=("express empty -> False; per tidied city, the number of rows with express False (171 False + 11 empty = "
                  "182 in total)."),
        av_notes="city may be a column.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 6}},
                    {'check': 'counts_sum_to_rows', 'args': {'column': '__values__', 'expected': 182}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': 240}}],
        direction='HARM',
        reason=("fillna(False) downcast express to a true/false column on 2.x, so ~ negates it; on 3.x the column stays generic "
                "and ~ turns True/False into -2/-1, giving negative counts."),
        naive='''import pandas as pd

df = pd.read_csv("deliveries.csv")
df["city"] = df["city"].str.strip().str.title()
df["express"] = df["express"].fillna(False)
result = (~df["express"]).groupby(df["city"]).sum()
''',
        ref=REF_DEL + '''counts = [sum(1 for r in rows if tidy(r["city"]) == c and r["express"] != "True") for c in cities]
result = pd.Series(np.array(counts, dtype="int64"), index=pd.Index(cities, name="city"))
'''),
    dict(
        id='M_QF6_09', row='N01', files=[DEL],
        text=("Encode status as 1 for shipped and 0 for pending in a column shipped. Give the Pearson correlation table of "
              "shipped and parcels (rows with an empty parcels cell are left out of that pair). `result` should be a 2 x 2 "
              "table with shipped and parcels as both row and column labels."),
        allowed=[], invited=['N01'], order=False, keys=[], dtype=False,
        intended=("Correlation matrix of the 1/0 shipped indicator and parcels over the rows where parcels is not empty "
                  "(pairwise complete); diagonal 1."),
        av_notes="row and column order of the two labels is free; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 2}},
                    {'check': 'columns_present', 'args': {'columns': ['shipped', 'parcels']}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['shipped', 'parcels'], 'min': -1, 'max': 1}}],
        direction='HARM',
        reason=("The replace() result was downcast to integers on 2.x and kept by corr(numeric_only=True); on 3.x it stays "
                "generic and is dropped, leaving a 1 x 1 table."),
        naive='''import pandas as pd

df = pd.read_csv("deliveries.csv")
df["shipped"] = df["status"].replace({"shipped": 1, "pending": 0})
result = df[["shipped", "parcels"]].corr(numeric_only=True)
''',
        ref=REF_DEL + '''pairs = [(1.0 if r["status"] == "shipped" else 0.0, float(r["parcels"])) for r in rows if r["parcels"].strip() != ""]
x = np.array([p[0] for p in pairs], dtype="float64")
y = np.array([p[1] for p in pairs], dtype="float64")
r = float(np.corrcoef(x, y)[0, 1])
result = pd.DataFrame(np.array([[1.0, r], [r, 1.0]], dtype="float64"), index=["shipped", "parcels"],
                      columns=["shipped", "parcels"])
'''),
    dict(
        id='M_QF6_13', row='N01', files=[DEL],
        text=("The deliveries are listed in time order. Fill each empty express cell with the express value of the previous "
              "delivery in the file. Tidy the city names (remove surrounding spaces and write each word with a capital first "
              "letter, as in 'Oslo'). For each city, give the share of express deliveries and the average number of parcels. "
              "`result` should be a table indexed by city with the columns express and parcels."),
        allowed=[], invited=['N01'], order=False, keys=[], dtype=False,
        intended=("Forward-fill express in file order (the first row is not empty), then per tidied city the mean of express "
                  "(True = 1) and the mean of the non-empty parcels values."),
        av_notes="city may be a column; shares as 0-1 values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 6}},
                    {'check': 'columns_present', 'args': {'columns': ['express', 'parcels']}},
                    {'check': 'rate_in_unit_interval', 'args': {'columns': ['express']}}],
        direction='HARM',
        reason=("ffill() downcast express to a true/false column on 2.x, which mean(numeric_only=True) keeps; on 3.x the "
                "filled column stays generic and is dropped."),
        naive='''import pandas as pd

df = pd.read_csv("deliveries.csv")
df["city"] = df["city"].str.strip().str.title()
df["express"] = df["express"].ffill()
result = df[["city", "express", "parcels"]].groupby("city").mean(numeric_only=True)
''',
        ref=REF_DEL + '''prev = None
filled = []
for r in rows:
    v = r["express"].strip()
    if v == "":
        v = prev
    filled.append(v == "True")
    prev = v
express, parcels = [], []
for c in cities:
    idx = [i for i, r in enumerate(rows) if tidy(r["city"]) == c]
    express.append(sum(1 for i in idx if filled[i]) / len(idx))
    p = [int(rows[i]["parcels"]) for i in idx if rows[i]["parcels"].strip() != ""]
    parcels.append(sum(p) / len(p))
result = pd.DataFrame({"express": np.array(express, dtype="float64"), "parcels": np.array(parcels, dtype="float64")},
                      index=pd.Index(cities, name="city"))
'''),
    # ------------------------------------------------------------ N02 (0/0 in nullable float is missing on 3.x)
    dict(
        id='M_QF6_02', row='N02', files=[ST],
        text=("Read sales and visits as whole-number columns that allow empty cells. The conversion rate of a store-day is "
              "sales divided by visits. How many store-days have no usable conversion rate, because visits is empty or "
              "zero? `result` should be that number."),
        allowed=[], invited=['N02'], order=False, keys=[], dtype=False,
        intended="Count rows where visits is empty (3 rows) or visits is 0 (3 rows, all with sales 0): 6.",
        av_notes="a whole number; a one-element Series is acceptable.",
        checks=G + [{'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': 90}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='FIX',
        reason=("With nullable columns, 0/0 gave NaN that isna() did not count on 2.x (3 instead of 6); on 3.x 0/0 is "
                "missing and the count is right."),
        naive='''import pandas as pd

df = pd.read_csv("store_traffic.csv", dtype_backend="numpy_nullable")
rate = df["sales"] / df["visits"]
result = int(rate.isna().sum())
''',
        ref=REF_ST + '''result = int(sum(1 for r in rows if rate(r) is None))
'''),
    dict(
        id='M_QF6_06', row='N02', files=[ST],
        text=("Keep sales and visits as whole-number columns that allow empty cells (convert the table to the best-fitting "
              "column types after reading). The conversion rate of a store-day is sales divided by visits; days with empty or "
              "zero visits have no usable rate and are skipped. For each store, give the average conversion rate over its "
              "usable days. `result` should be a Series indexed by store."),
        allowed=[], invited=['N02'], order=False, keys=[], dtype=False,
        intended=("Per store (30 stores, 3 days each), the mean of sales/visits over the days whose visits is non-empty and "
                  "non-zero."),
        av_notes="store may be a column; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 30}},
                    {'check': 'no_nulls', 'args': {'columns': []}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}}],
        direction='FIX',
        reason=("On 2.x the 0/0 days were NaN values inside the nullable column, so the store mean became NaN; on 3.x they are "
                "missing and skipped as the task asks."),
        naive='''import pandas as pd

df = pd.read_csv("store_traffic.csv").convert_dtypes()
df["rate"] = df["sales"] / df["visits"]
result = df.groupby("store")["rate"].mean()
''',
        ref=REF_ST + '''stores = sorted({r["store"] for r in rows})
means = []
for s in stores:
    vals = [rate(r) for r in rows if r["store"] == s and rate(r) is not None]
    means.append(sum(vals) / len(vals))
result = pd.Series(np.array(means, dtype="float64"), index=pd.Index(stores, name="store"))
'''),
    dict(
        id='M_QF6_10', row='N02', files=[ST],
        text=("Keep sales and visits as whole-number columns that allow empty cells (convert the table to the best-fitting "
              "column types after reading). The conversion rate of a store-day is sales divided by visits. Count a "
              "store-day without a usable rate (empty or zero visits) as rate 0, and give the average rate over all "
              "store-days. `result` should be that number."),
        allowed=[], invited=['N02'], order=False, keys=[], dtype=False,
        intended="Mean over all 90 rows of sales/visits, where rows with empty or zero visits contribute 0.",
        av_notes="to 6 significant digits; a one-element Series is acceptable.",
        checks=G + [{'check': 'no_nulls', 'args': {'columns': []}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='FIX',
        reason=("fillna(0) did not reach the NaN produced by 0/0 in the nullable column on 2.x, so the mean was NaN; on 3.x "
                "0/0 is missing, gets filled, and the mean is the requested number."),
        naive='''import pandas as pd

df = pd.read_csv("store_traffic.csv").convert_dtypes()
rate = df["sales"] / df["visits"]
result = rate.fillna(0).mean()
''',
        ref=REF_ST + '''vals = [rate(r) if rate(r) is not None else 0.0 for r in rows]
result = float(sum(vals) / len(vals))
'''),
    dict(
        id='M_QF6_14', row='N02', files=[ST],
        text=("Read sales and visits as whole-number columns that allow empty cells. The conversion rate of a store-day is "
              "sales divided by visits; leave out days with empty or zero visits. Which three store-days have the highest "
              "conversion rate? `result` should be a table with the columns store and rate, highest rate first."),
        allowed=[], invited=['N02'], order=True, keys=['rate'], dtype=False,
        intended=("Among the 84 rows with a usable rate, the three rows with the largest sales/visits, sorted descending, "
                  "with store and rate."),
        av_notes="row labels (index) are free; rates to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 3}},
                    {'check': 'columns_present', 'args': {'columns': ['store', 'rate']}},
                    {'check': 'no_nulls', 'args': {'columns': ['rate']}},
                    {'check': 'sorted_by', 'args': {'keys': ['rate'], 'ascending': [False]}}],
        direction='FIX',
        reason=("On 2.x the 0/0 days held NaN values that sorted as the largest rates and filled the top three; on 3.x they "
                "are missing and sorted last."),
        naive='''import pandas as pd

df = pd.read_csv("store_traffic.csv", dtype_backend="numpy_nullable")
df["rate"] = df["sales"] / df["visits"]
result = df.sort_values("rate", ascending=False).head(3)[["store", "rate"]].reset_index(drop=True)
''',
        ref=REF_ST + '''usable = [(r["store"], rate(r)) for r in rows if rate(r) is not None]
top = sorted(usable, key=lambda p: -p[1])[:3]
result = pd.DataFrame({"store": [p[0] for p in top], "rate": np.array([p[1] for p in top], dtype="float64")})
'''),
    # ------------------------------------------------------------ N05 (frame vs nullable Series comparison keeps NA on 3.1)
    dict(
        id='M_QF6_03', row='N05', files=[QZ],
        text=("The pass marks are 6 points for quiz_a and 5 points for quiz_b. An empty cell means the student was absent, "
              "and an absent student did not reach the pass mark. For each quiz, give the share of all 80 students who "
              "reached the pass mark (score at or above it). `result` should be a Series indexed by quiz."),
        allowed=[], invited=['N05'], order=False, keys=[], dtype=False,
        intended=("quiz_a: number of scores >= 6 divided by 80; quiz_b: number of scores >= 5 divided by 80 (absent students "
                  "count in the denominator)."),
        av_notes="shares as 0-1 values to 6 significant digits; quiz may be a column.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 2}},
                    {'check': 'rate_in_unit_interval', 'args': {'columns': ['__values__']}}],
        direction='HARM',
        reason=("Comparing the scores with a nullable pass-mark Series gave False for absent students on 2.x (counted in the "
                "denominator); on 3.1 it gives missing values that mean() skips, raising the shares."),
        naive=NAIVE_QZ_MARKS + '''result = (df >= marks).mean()
''',
        ref=REF_QZ + '''marks = {"quiz_a": 6, "quiz_b": 5}
shares = [sum(1 for v in score[q] if v is not None and v >= marks[q]) / len(rows) for q in QUIZZES]
result = pd.Series(np.array(shares, dtype="float64"), index=QUIZZES)
'''),
    dict(
        id='M_QF6_07', row='N05', files=[QZ],
        text=("The pass marks are 6 points for quiz_a and 5 points for quiz_b. An empty cell means the student was absent, "
              "and an absent student did not reach the pass mark. How many students reached the pass mark in both quizzes? "
              "`result` should be that number."),
        allowed=[], invited=['N05'], order=False, keys=[], dtype=False,
        intended="Number of rows with quiz_a >= 6 and quiz_b >= 5, both non-empty.",
        av_notes="a whole number.",
        checks=G + [{'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': 80}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='HARM',
        reason=("On 2.x an absent student's comparison was False, so all(axis=1) excluded them; on 3.1 it is missing and "
                "all() skips it, so students absent in one quiz who passed the other are counted."),
        naive=NAIVE_QZ_MARKS + '''passed = df >= marks
result = int(passed.all(axis=1).sum())
''',
        ref=REF_QZ + '''marks = {"quiz_a": 6, "quiz_b": 5}
result = int(sum(1 for i in range(len(rows))
                 if all(score[q][i] is not None and score[q][i] >= marks[q] for q in QUIZZES)))
'''),
    dict(
        id='M_QF6_11', row='N05', files=[QZ],
        text=("The pass marks are 6 points for quiz_a and 5 points for quiz_b; an empty cell means the student was absent "
              "from that quiz. For each quiz, give the share of the students who took it (non-empty cell) whose score is at "
              "or above the pass mark. `result` should be a Series indexed by quiz."),
        allowed=[], invited=['N05'], order=False, keys=[], dtype=False,
        intended=("quiz_a: scores >= 6 divided by the 73 non-empty quiz_a cells; quiz_b: scores >= 5 divided by the 75 "
                  "non-empty quiz_b cells."),
        av_notes="shares as 0-1 values to 6 significant digits; quiz may be a column.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 2}},
                    {'check': 'rate_in_unit_interval', 'args': {'columns': ['__values__']}}],
        direction='FIX',
        reason=("The comparison with a nullable pass-mark Series gives missing values for absent students on 3.1, which mean() "
                "skips as the task asks; on 2.x they were False and counted in the denominator."),
        naive=NAIVE_QZ_MARKS + '''result = (df >= marks).mean()
''',
        ref=REF_QZ + '''marks = {"quiz_a": 6, "quiz_b": 5}
shares = []
for q in QUIZZES:
    taken = [v for v in score[q] if v is not None]
    shares.append(sum(1 for v in taken if v >= marks[q]) / len(taken))
result = pd.Series(np.array(shares, dtype="float64"), index=QUIZZES)
'''),
    dict(
        id='M_QF6_15', row='N05', files=[QZ],
        text=("The pass marks are 6 points for quiz_a and 5 points for quiz_b; an empty cell means the student was absent "
              "from that quiz, and an absence is not a fail. How many students scored below the pass mark in at least one "
              "quiz they took? `result` should be that number."),
        allowed=[], invited=['N05'], order=False, keys=[], dtype=False,
        intended="Number of rows with (quiz_a non-empty and < 6) or (quiz_b non-empty and < 5).",
        av_notes="a whole number.",
        checks=G + [{'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': 80}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='FIX',
        reason=("On 2.x the comparison was False for an absence, so negating it counted absences as fails; on 3.1 it is "
                "missing and any() skips it, as the task asks."),
        naive=NAIVE_QZ_MARKS + '''passed = df >= marks
result = int((~passed).any(axis=1).sum())
''',
        ref=REF_QZ + '''marks = {"quiz_a": 6, "quiz_b": 5}
result = int(sum(1 for i in range(len(rows))
                 if any(score[q][i] is not None and score[q][i] < marks[q] for q in QUIZZES)))
'''),
    # ------------------------------------------------------------ N06 (rank keeps NA on nullable columns)
    dict(
        id='M_QF6_04', row='N06', files=[QZ],
        text=("Read the scores as whole-number columns that allow empty cells. For quiz_a, give each student's percentile "
              "rank: rank the students who took the quiz from the lowest score (equal scores share the average of their "
              "ranks) and divide by the number of students who took it. Absent students (empty cell) get no rank. `result` "
              "should be a Series with one value per student in file order."),
        allowed=[], invited=['N06'], order=False, keys=[], dtype=False,
        intended=("Average ranks (ascending) of the 73 non-empty quiz_a scores divided by 73; missing for the 7 absent "
                  "students; 80 values in file order."),
        av_notes="missing values in any null representation; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 80}},
                    {'check': 'rate_in_unit_interval', 'args': {'columns': ['__values__']}}],
        direction='FIX',
        reason=("On 2.x rank() on a nullable column gave the absent students a rank and shifted everybody else's; on 3.x "
                "absent students stay missing and the percentiles use the students who took the quiz."),
        naive='''import pandas as pd

df = pd.read_csv("quiz_scores.csv", dtype_backend="numpy_nullable")
result = df["quiz_a"].rank(pct=True)
''',
        ref=REF_RANK + '''r = avg_ranks(score["quiz_a"])
n = sum(1 for v in score["quiz_a"] if v is not None)
result = pd.Series(np.array([np.nan if x is None else x / n for x in r], dtype="float64"))
'''),
    dict(
        id='M_QF6_08', row='N06', files=[QZ],
        text=("Convert the table to the best-fitting column types after reading, so that the scores stay whole numbers with "
              "empty cells. Rank the students in quiz_b from the lowest score (rank 1 = lowest; equal scores share the "
              "average of their ranks). Absent students (empty cell) get no rank. `result` should be a Series with one rank "
              "per student in file order."),
        allowed=[], invited=['N06'], order=False, keys=[], dtype=False,
        intended="Average ascending ranks of the 75 non-empty quiz_b scores, missing for the 5 absent students; 80 values.",
        av_notes="missing values in any null representation.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 80}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 1, 'max': 75}}],
        direction='FIX',
        reason=("rank() on the nullable column ranked the absent students on 2.x and moved all ranks up; on 3.x they stay "
                "missing, as requested."),
        naive='''import pandas as pd

df = pd.read_csv("quiz_scores.csv").convert_dtypes()
result = df["quiz_b"].rank()
''',
        ref=REF_RANK + '''r = avg_ranks(score["quiz_b"])
result = pd.Series(np.array([np.nan if x is None else x for x in r], dtype="float64"))
'''),
    dict(
        id='M_QF6_12', row='N06', files=[QZ],
        text=("Read both quiz columns as whole numbers that allow empty cells. Rank the students in quiz_a from the top: "
              "rank 1 is the highest score, and equal scores all get the best rank of their group (for example 1, 1, 3). "
              "Absent students (empty cell) get no rank. `result` should be a Series with one rank per student in file "
              "order."),
        allowed=[], invited=['N06'], order=False, keys=[], dtype=False,
        intended=("Minimum-method descending ranks of the 73 non-empty quiz_a scores; missing for the 7 absent students; 80 "
                  "values in file order."),
        av_notes="missing values in any null representation; ranks may be whole numbers or decimals.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 80}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 1, 'max': 73}}],
        direction='FIX',
        reason=("On 2.x rank() on the nullable column also ranked the absent students (at the bottom); on 3.x they stay "
                "missing as the task asks."),
        naive='''import pandas as pd

df = pd.read_csv("quiz_scores.csv", dtype="Int64")
result = df["quiz_a"].rank(method="min", ascending=False)
''',
        ref=REF_RANK + '''r = min_ranks(score["quiz_a"], ascending=False)
result = pd.Series(np.array([np.nan if x is None else x for x in r], dtype="float64"))
'''),
    dict(
        id='M_QF6_16', row='N06', files=[QZ],
        text=("Convert the table to the best-fitting column types after reading, so that the scores stay whole numbers with "
              "empty cells. Rank the students in quiz_a from the lowest score (rank 1 = lowest; equal scores share the "
              "average of their ranks; absent students get no rank). Give the ranks of the students who scored 9 or 10 "
              "points in quiz_a. `result` should be a Series of ranks indexed by row position (0 = first student in the "
              "file), in file order."),
        allowed=[], invited=['N06'], order=False, keys=[], dtype=False,
        intended=("Average ascending ranks of the 73 non-empty quiz_a scores; keep the 8 students with quiz_a 9 or 10, "
                  "indexed by their 0-based row position."),
        av_notes="ranks may be decimals or whole numbers; row positions may be a column.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 8}},
                    {'check': 'no_nulls', 'args': {'columns': []}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 1, 'max': 73}}],
        direction='FIX',
        reason=("On 2.x rank() on the nullable column gave the absent students ranks below everybody, so every present "
                "student's rank rose by 7; on 3.x absent students stay unranked, as the task asks."),
        naive='''import pandas as pd

df = pd.read_csv("quiz_scores.csv").convert_dtypes()
ranks = df["quiz_a"].rank()
result = ranks[df["quiz_a"] >= 9]
''',
        ref=REF_RANK + '''r = avg_ranks(score["quiz_a"])
pos = [i for i, v in enumerate(score["quiz_a"]) if v is not None and v >= 9]
result = pd.Series(np.array([r[i] for i in pos], dtype="float64"), index=pd.Index(np.array(pos, dtype="int64")))
'''),
]
