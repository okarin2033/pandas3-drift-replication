# Task specifications for family QF8_NUMERIC (package TASKS_M2). Written 2026-11-11 by pkg:TASKS_M2.
# Status: prepared. Consumed by build.py (writes tasks/M2/<id>/).
# Rows and slots from mechanisms/confirm/quota_allocation.tsv: X01 -> odd slots 01-15; X02 -> even slots 02-16.

DT = 'QF8_NUMERIC/daily_temps.csv'
PS = 'QF8_NUMERIC/panel_scores.csv'

G = [{'check': 'no_null_text', 'args': {}}, {'check': 'no_all_missing_column', 'args': {}}]
PANELS = ['bread', 'cheese', 'cider', 'honey', 'jam', 'pickles', 'pies', 'soup']
SEM_DEF = ("The standard error of the mean of a window is the sample standard deviation of its values (dividing by n - 1) "
           "divided by the square root of n, the number of values in the window. ")

REF_DT = '''import csv
import math
import numpy as np
import pandas as pd

with open("daily_temps.csv", encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))
dates = [r["date"] for r in rows]
temp = [float(r["temp_c"]) if r["temp_c"].strip() != "" else None for r in rows]
hum = [float(r["humidity"]) if r["humidity"].strip() != "" else None for r in rows]


def sem(values):
    """sample sd / sqrt(n) of a list of floats (n >= 2)."""
    a = np.array(values, dtype="float64")
    return float(np.std(a, ddof=1) / math.sqrt(len(a)))


def rolling_sem(vals, window, min_periods=None):
    """Trailing windows of `window` rows; None when fewer than min_periods (default: window) values are present."""
    need = window if min_periods is None else min_periods
    out = []
    for i in range(len(vals)):
        win = [v for v in vals[max(0, i - window + 1):i + 1] if v is not None]
        out.append(sem(win) if len(win) >= max(need, 2) else None)
    return out


def date_index(ds):
    return pd.DatetimeIndex(pd.to_datetime(ds, format="%Y-%m-%d"), name="date")


def as_float(vals):
    return np.array([np.nan if v is None else v for v in vals], dtype="float64")
'''

REF_PS = '''import csv
import numpy as np
import pandas as pd

with open("panel_scores.csv", encoding="utf-8", newline="") as f:
    rows = [(r["panel"], r["entrant"], float(r["score"])) for r in csv.DictReader(f)]
panels = sorted({p for p, _, _ in rows})


def middle(scores, tie):
    """The score at the middle position of the sorted scores; with an even count the two middle scores are equally near
    and `tie` ('lower' or 'higher') picks one."""
    s = sorted(scores)
    n = len(s)
    if n % 2 == 1:
        return s[n // 2]
    return s[n // 2 - 1] if tie == "lower" else s[n // 2]


def nearest_pos(scores, q):
    """Score at the sorted position nearest to q * (n - 1) (counting from 0); only used where that position is not a tie."""
    s = sorted(scores)
    return s[int(round(q * (len(s) - 1)))]


by_panel = {p: [sc for pp, _, sc in rows if pp == p] for p in panels}
'''

NAIVE_DT = '''import pandas as pd

df = pd.read_csv("daily_temps.csv", parse_dates=["date"])
df = df.set_index("date")
'''

NAIVE_PS = '''import pandas as pd

df = pd.read_csv("panel_scores.csv")
middle = df.groupby("panel")["score"].quantile(0.5, interpolation="nearest")
'''

MID_HI = ("The 'middle score' of a panel is the score actually given that sits in the middle of the panel's sorted scores; "
          "each panel has 12 entries, so two scores are equally near the middle, and then the higher of the two is used. ")
MID_LO = ("The 'middle score' of a panel is the score actually given that sits in the middle of the panel's sorted scores; "
          "each panel has 12 entries, so two scores are equally near the middle, and then the lower of the two is used. ")

SPECS = [
    # ------------------------------------------------------------ X01 (rolling / expanding sem formula fixed in 3.0)
    dict(
        id='M_QF8_01', row='X01', files=[DT],
        text=(SEM_DEF + "For each day, give the standard error of the mean temperature over a 7-day window (that day and the "
              "6 days before it); leave it empty when the window has fewer than 7 temperatures. `result` should be a Series "
              "indexed by date."),
        allowed=[], invited=['X01'], order=False, keys=[], dtype=False,
        intended=("For each of the 90 days, the trailing 7-row window of temp_c (rows are consecutive days); if all 7 values "
                  "are present, sample sd / sqrt(7), otherwise missing (the first 6 days and the windows containing the one "
                  "empty temperature)."),
        av_notes="date may be a column; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 90}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['date'], 'min_year': 2025, 'max_year': 2025}}],
        direction='FIX',
        reason=("rolling().sem() divided the sample sd by sqrt(n - 1) on 2.x; 3.x divides by sqrt(n), the definition given in "
                "the task."),
        naive=NAIVE_DT + '''result = df["temp_c"].rolling(7).sem()
''',
        ref=REF_DT + '''result = pd.Series(as_float(rolling_sem(temp, 7)), index=date_index(dates))
'''),
    dict(
        id='M_QF8_03', row='X01', files=[DT],
        text=(SEM_DEF + "For each day, take the 7-day window of temperatures (that day and the 6 days before it) and give the "
              "window mean and a band of the mean minus and plus 1.96 standard errors of the mean; leave all three empty "
              "when the window has fewer than 7 temperatures. `result` should be a table indexed by date with the columns "
              "mean, lower and upper."),
        allowed=[], invited=['X01'], order=False, keys=[], dtype=False,
        intended=("For each day with 7 present values in the trailing 7-row window: mean, mean - 1.96 * sd/sqrt(7) and "
                  "mean + 1.96 * sd/sqrt(7) (sd with n - 1); missing otherwise."),
        av_notes="date may be a column; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 90}},
                    {'check': 'columns_present', 'args': {'columns': ['mean', 'lower', 'upper']}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['date'], 'min_year': 2025, 'max_year': 2025}}],
        direction='FIX',
        reason=("The band uses rolling().sem(), which was too wide on 2.x (sd / sqrt(n - 1)); 3.x uses sd / sqrt(n) as "
                "defined in the task."),
        naive=NAIVE_DT + '''roll = df["temp_c"].rolling(7)
mean = roll.mean()
se = roll.sem()
result = pd.DataFrame({"mean": mean, "lower": mean - 1.96 * se, "upper": mean + 1.96 * se})
''',
        ref=REF_DT + '''means, lows, ups = [], [], []
for i in range(len(temp)):
    win = temp[max(0, i - 6):i + 1]
    if i >= 6 and all(v is not None for v in win):
        m = float(np.mean(np.array(win, dtype="float64")))
        e = sem(win)
        means.append(m); lows.append(m - 1.96 * e); ups.append(m + 1.96 * e)
    else:
        means.append(None); lows.append(None); ups.append(None)
result = pd.DataFrame({"mean": as_float(means), "lower": as_float(lows), "upper": as_float(ups)}, index=date_index(dates))
'''),
    dict(
        id='M_QF8_05', row='X01', files=[DT],
        text=(SEM_DEF + "For each day, give the standard error of the mean humidity over a 10-day window (that day and the 9 "
              "days before it); leave it empty for the first 9 days. `result` should be a Series indexed by date."),
        allowed=[], invited=['X01'], order=False, keys=[], dtype=False,
        intended="For each day from the 10th on: sample sd of the 10 humidity values in the trailing window / sqrt(10).",
        av_notes="date may be a column; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 90}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['date'], 'min_year': 2025, 'max_year': 2025}}],
        direction='FIX',
        reason="rolling().sem() used sqrt(n - 1) on 2.x; 3.x uses sqrt(n), the definition given in the task.",
        naive=NAIVE_DT + '''result = df["humidity"].rolling(10).sem()
''',
        ref=REF_DT + '''result = pd.Series(as_float(rolling_sem(hum, 10)), index=date_index(dates))
'''),
    dict(
        id='M_QF8_07', row='X01', files=[DT],
        text=(SEM_DEF + "Using 7-day windows of temperature (each day and the 6 days before it; only windows with 7 "
              "temperatures count), on how many days does the standard error of the mean exceed 0.8 degrees? `result` "
              "should be that number."),
        allowed=[], invited=['X01'], order=False, keys=[], dtype=False,
        intended="Count of days whose complete trailing 7-day window has sample sd / sqrt(7) > 0.8.",
        av_notes="a whole number.",
        checks=G + [{'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': 90}},
                    {'check': 'result_kind', 'args': {'kind': 'scalar'}}],
        direction='FIX',
        reason=("rolling().sem() was larger on 2.x (sqrt(n - 1) divisor), so more days crossed the threshold; 3.x follows the "
                "task's definition."),
        naive=NAIVE_DT + '''se = df["temp_c"].rolling(7).sem()
result = int((se > 0.8).sum())
''',
        ref=REF_DT + '''result = int(sum(1 for v in rolling_sem(temp, 7) if v is not None and v > 0.8))
'''),
    dict(
        id='M_QF8_09', row='X01', files=[DT],
        text=(SEM_DEF + "For each of the first 30 days, give the standard error of the mean temperature over all days from "
              "the first day up to that day (empty temperatures skipped; leave it empty while fewer than 2 temperatures are "
              "available). `result` should be a Series indexed by date with 30 values."),
        allowed=[], invited=['X01'], order=False, keys=[], dtype=False,
        intended=("Expanding window from 2025-06-01: for day k (1-30), sample sd / sqrt(n) of the n present temperatures of "
                  "days 1..k; missing for day 1."),
        av_notes="date may be a column; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 30}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['date'], 'min_year': 2025, 'max_year': 2025}}],
        direction='FIX',
        reason="expanding().sem() divided by sqrt(n - 1) on 2.x; 3.x divides by sqrt(n) as the task defines.",
        naive=NAIVE_DT + '''result = df["temp_c"].expanding(min_periods=2).sem().head(30)
''',
        ref=REF_DT + '''out = []
for i in range(30):
    vals = [v for v in temp[:i + 1] if v is not None]
    out.append(sem(vals) if len(vals) >= 2 else None)
result = pd.Series(as_float(out), index=date_index(dates[:30]))
'''),
    dict(
        id='M_QF8_11', row='X01', files=[DT],
        text=(SEM_DEF + "For each day, give the standard error of the mean of temp_c and of humidity over a 14-day window "
              "(that day and the 13 days before it); leave a value empty when its window has fewer than 14 values. `result` "
              "should be a table indexed by date with the columns temp_c and humidity."),
        allowed=[], invited=['X01'], order=False, keys=[], dtype=False,
        intended=("Separately for temp_c and humidity: for each day whose trailing 14-row window has 14 present values, "
                  "sample sd / sqrt(14); missing otherwise."),
        av_notes="date may be a column; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 90}},
                    {'check': 'columns_present', 'args': {'columns': ['temp_c', 'humidity']}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['temp_c', 'humidity'], 'min': 0, 'max': None}}],
        direction='FIX',
        reason="rolling().sem() on the table used sqrt(n - 1) on 2.x; 3.x uses sqrt(n) as the task defines.",
        naive=NAIVE_DT + '''result = df[["temp_c", "humidity"]].rolling(14).sem()
''',
        ref=REF_DT + '''result = pd.DataFrame({"temp_c": as_float(rolling_sem(temp, 14)), "humidity": as_float(rolling_sem(hum, 14))},
                      index=date_index(dates))
'''),
    dict(
        id='M_QF8_13', row='X01', files=[DT],
        text=(SEM_DEF + "Use calendar windows: for each date, the window holds the temperatures of that date and the 6 "
              "calendar days before it (empty temperatures skipped). Give the standard error of the mean temperature for "
              "every date whose window has at least 3 temperatures, and leave it empty otherwise. `result` should be a "
              "Series indexed by date."),
        allowed=[], invited=['X01'], order=False, keys=[], dtype=False,
        intended=("Time-based window of 7 calendar days ending on each date (the file has no missing dates); sample sd / "
                  "sqrt(n) of the n present temperatures when n >= 3, missing otherwise."),
        av_notes="date may be a column; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 90}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['date'], 'min_year': 2025, 'max_year': 2025}}],
        direction='FIX',
        reason=("The time-based rolling().sem() divided by sqrt(n - 1) on 2.x; 3.x divides by sqrt(n) as the task "
                "defines."),
        naive=NAIVE_DT + '''result = df["temp_c"].rolling("7D", min_periods=3).sem()
''',
        ref=REF_DT + '''result = pd.Series(as_float(rolling_sem(temp, 7, min_periods=3)), index=date_index(dates))
'''),
    dict(
        id='M_QF8_15', row='X01', files=[DT],
        text=(SEM_DEF + "For each day, use a centred 5-day window (the day, the 2 days before and the 2 days after) and give "
              "the standard error of the mean temperature; leave it empty when the window does not have 5 temperatures. "
              "`result` should be a Series indexed by date."),
        allowed=[], invited=['X01'], order=False, keys=[], dtype=False,
        intended=("For each day with 2 days on either side and 5 present values in rows i-2..i+2: sample sd / sqrt(5); "
                  "missing otherwise (first 2 and last 2 days, windows with the empty temperature)."),
        av_notes="date may be a column; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 90}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': None}},
                    {'check': 'date_year_in_range', 'args': {'columns': ['date'], 'min_year': 2025, 'max_year': 2025}}],
        direction='FIX',
        reason="The centred rolling().sem() used sqrt(n - 1) on 2.x; 3.x uses sqrt(n), the task's definition.",
        naive=NAIVE_DT + '''result = df["temp_c"].rolling(5, center=True).sem()
''',
        ref=REF_DT + '''out = []
for i in range(len(temp)):
    win = temp[i - 2:i + 3] if 2 <= i <= len(temp) - 3 else []
    out.append(sem(win) if len(win) == 5 and all(v is not None for v in win) else None)
result = pd.Series(as_float(out), index=date_index(dates))
'''),
    # ------------------------------------------------------------ X02 (groupby quantile(0.5, interpolation='nearest'))
    dict(
        id='M_QF8_02', row='X02', files=[PS],
        text=(MID_HI + "Give the middle score of each panel. `result` should be a Series indexed by panel."),
        allowed=[], invited=['X02'], order=False, keys=[], dtype=False,
        intended="Per panel (8 panels of 12), the 7th smallest score (the higher of the two middle scores).",
        av_notes="panel may be a column.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 8}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 4, 'max': 10}},
                    {'check': 'values_in_set', 'args': {'column': 'panel', 'values': PANELS}}],
        direction='FIX',
        reason=("groupby().quantile(0.5, interpolation='nearest') took the lower middle score on 2.x and the higher one on "
                "3.x, and the task asks for the higher one."),
        naive=NAIVE_PS + '''result = middle
''',
        ref=REF_PS + '''result = pd.Series(np.array([middle(by_panel[p], "higher") for p in panels], dtype="float64"),
                   index=pd.Index(panels, name="panel"))
'''),
    dict(
        id='M_QF8_04', row='X02', files=[PS],
        text=("For each panel, give three scores actually given: the score at the position nearest to the lower quartile, "
              "the middle score and the score nearest to the upper quartile, where the position of a quartile q is q x (n - "
              "1) counting the sorted scores from 0. Each panel has 12 entries, so two scores are equally near the middle "
              "position; then use the lower of the two. `result` should be a table indexed by panel with the columns q1, "
              "middle and q3."),
        allowed=[], invited=['X02'], order=False, keys=[], dtype=False,
        intended=("Per panel with sorted scores s[0..11]: q1 = s[3] (position 2.75), middle = s[5] (position 5.5, lower "
                  "neighbour), q3 = s[8] (position 8.25)."),
        av_notes="panel may be a column; a long table with a quartile column is acceptable.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 8}},
                    {'check': 'columns_present', 'args': {'columns': ['q1', 'middle', 'q3']}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['q1', 'middle', 'q3'], 'min': 4, 'max': 10}}],
        direction='HARM',
        reason=("groupby().quantile([...], interpolation='nearest') returned the lower middle score at 0.5 on 2.x, as the "
                "task asks; 3.x returns the higher one."),
        naive='''import pandas as pd

df = pd.read_csv("panel_scores.csv")
q = df.groupby("panel")["score"].quantile([0.25, 0.5, 0.75], interpolation="nearest").unstack()
q.columns = ["q1", "middle", "q3"]
result = q
''',
        ref=REF_PS + '''result = pd.DataFrame({"q1": np.array([nearest_pos(by_panel[p], 0.25) for p in panels], dtype="float64"),
                       "middle": np.array([middle(by_panel[p], "lower") for p in panels], dtype="float64"),
                       "q3": np.array([nearest_pos(by_panel[p], 0.75) for p in panels], dtype="float64")},
                      index=pd.Index(panels, name="panel"))
'''),
    dict(
        id='M_QF8_06', row='X02', files=[PS],
        text=(MID_HI + "For each panel, count the entrants who scored strictly above the panel's middle score. `result` "
              "should be a Series of counts indexed by panel."),
        allowed=[], invited=['X02'], order=False, keys=[], dtype=False,
        intended="Per panel, the number of rows with score > the 7th smallest score of that panel.",
        av_notes="panel may be a column; a panel with no such entrant shows 0.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 8}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 0, 'max': 12}}],
        direction='FIX',
        reason=("The threshold from groupby().quantile(0.5, interpolation='nearest') was the lower middle score on 2.x, "
                "counting one entrant too many in most panels; 3.x gives the higher one requested."),
        naive=NAIVE_PS + '''above = df["score"] > df["panel"].map(middle)
result = above.groupby(df["panel"]).sum()
''',
        ref=REF_PS + '''counts = [sum(1 for sc in by_panel[p] if sc > middle(by_panel[p], "higher")) for p in panels]
result = pd.Series(np.array(counts, dtype="int64"), index=pd.Index(panels, name="panel"))
'''),
    dict(
        id='M_QF8_08', row='X02', files=[PS],
        text=(MID_LO + "For each panel, give the lowest score, the middle score and the highest score. `result` should be a "
              "table indexed by panel with the columns lowest, middle and highest."),
        allowed=[], invited=['X02'], order=False, keys=[], dtype=False,
        intended="Per panel: min, 6th smallest score (lower middle), max.",
        av_notes="panel may be a column.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 8}},
                    {'check': 'columns_present', 'args': {'columns': ['lowest', 'middle', 'highest']}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['lowest', 'middle', 'highest'], 'min': 4, 'max': 10}}],
        direction='HARM',
        reason=("groupby().quantile(0.5, interpolation='nearest') gave the lower middle score on 2.x, as requested; 3.x "
                "gives the higher one."),
        naive=NAIVE_PS + '''g = df.groupby("panel")["score"]
result = pd.DataFrame({"lowest": g.min(), "middle": middle, "highest": g.max()})
''',
        ref=REF_PS + '''result = pd.DataFrame({"lowest": np.array([min(by_panel[p]) for p in panels], dtype="float64"),
                       "middle": np.array([middle(by_panel[p], "lower") for p in panels], dtype="float64"),
                       "highest": np.array([max(by_panel[p]) for p in panels], dtype="float64")},
                      index=pd.Index(panels, name="panel"))
'''),
    dict(
        id='M_QF8_10', row='X02', files=[PS],
        text=(MID_HI + "Rank the panels by their middle score, highest first. `result` should be a Series of middle scores "
              "indexed by panel, sorted from the highest middle score to the lowest."),
        allowed=[], invited=['X02'], order=True, keys=['__values__'], dtype=False,
        intended="Per panel the 7th smallest score, sorted descending (ties in any order).",
        av_notes="panel may be a column with a middle-score column.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 8}},
                    {'check': 'sorted_by', 'args': {'keys': ['__values__'], 'ascending': [False]}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': 4, 'max': 10}}],
        direction='FIX',
        reason=("groupby().quantile(0.5, interpolation='nearest') gave the lower middle score on 2.x; 3.x gives the higher "
                "one the task asks for, which changes values and order."),
        naive=NAIVE_PS + '''result = middle.sort_values(ascending=False)
''',
        ref=REF_PS + '''pairs = sorted(((middle(by_panel[p], "higher"), p) for p in panels), key=lambda t: (-t[0], t[1]))
result = pd.Series(np.array([v for v, _ in pairs], dtype="float64"), index=pd.Index([p for _, p in pairs], name="panel"))
'''),
    dict(
        id='M_QF8_12', row='X02', files=[PS],
        text=(MID_LO + "List the entries whose score equals their panel's middle score. `result` should be a table with the "
              "columns panel, entrant (surrounding spaces removed) and score, in file order."),
        allowed=[], invited=['X02'], order=False, keys=[], dtype=False,
        intended="Rows whose score equals the 6th smallest score of their panel, with panel, stripped entrant and score.",
        av_notes="row labels and row order are free; entrant capitalisation may be tidied.",
        checks=G + [{'check': 'columns_present', 'args': {'columns': ['panel', 'entrant', 'score']}},
                    {'check': 'values_in_set', 'args': {'column': 'panel', 'values': PANELS}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['score'], 'min': 4, 'max': 10}}],
        direction='HARM',
        reason=("The middle score from groupby().quantile(0.5, interpolation='nearest') was the lower one on 2.x, as the task "
                "says; on 3.x the higher one selects other entries."),
        naive=NAIVE_PS + '''df["entrant"] = df["entrant"].str.strip()
hits = df[df["score"] == df["panel"].map(middle)]
result = hits[["panel", "entrant", "score"]].reset_index(drop=True)
''',
        ref=REF_PS + '''mid = {p: middle(by_panel[p], "lower") for p in panels}
sel = [(p, e.strip(), sc) for p, e, sc in rows if sc == mid[p]]
result = pd.DataFrame({"panel": [s[0] for s in sel], "entrant": [s[1] for s in sel],
                       "score": np.array([s[2] for s in sel], dtype="float64")})
'''),
    dict(
        id='M_QF8_14', row='X02', files=[PS],
        text=(MID_HI + "For each panel, give the mean score minus the middle score. `result` should be a Series indexed by "
              "panel."),
        allowed=[], invited=['X02'], order=False, keys=[], dtype=False,
        intended="Per panel: arithmetic mean of its 12 scores minus its 7th smallest score.",
        av_notes="panel may be a column; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 8}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': -6, 'max': 6}}],
        direction='FIX',
        reason=("The middle score from groupby().quantile(0.5, interpolation='nearest') was the lower one on 2.x; 3.x uses "
                "the higher one that the task specifies."),
        naive=NAIVE_PS + '''result = df.groupby("panel")["score"].mean() - middle
''',
        ref=REF_PS + '''vals = [float(np.mean(np.array(by_panel[p], dtype="float64"))) - middle(by_panel[p], "higher") for p in panels]
result = pd.Series(np.array(vals, dtype="float64"), index=pd.Index(panels, name="panel"))
'''),
    dict(
        id='M_QF8_16', row='X02', files=[PS],
        text=(MID_LO + "For every entry, give its score minus the middle score of its panel. `result` should be a Series with "
              "one value per entry in file order."),
        allowed=[], invited=['X02'], order=False, keys=[], dtype=False,
        intended="96 values in file order: score minus the 6th smallest score of the entry's panel.",
        av_notes="row labels are free; values to 6 significant digits.",
        checks=G + [{'check': 'n_groups_equals', 'args': {'n': 96}},
                    {'check': 'numeric_in_range', 'args': {'columns': ['__values__'], 'min': -6, 'max': 6}}],
        direction='HARM',
        reason=("groupby().quantile(0.5, interpolation='nearest') gave the lower middle score on 2.x as requested; on 3.x the "
                "higher one shifts the differences of most panels."),
        naive=NAIVE_PS + '''result = df["score"] - df["panel"].map(middle)
''',
        ref=REF_PS + '''mid = {p: middle(by_panel[p], "lower") for p in panels}
result = pd.Series(np.array([sc - mid[p] for p, _, sc in rows], dtype="float64"))
'''),
]
