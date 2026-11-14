# Task specifications for family QF4_GROUPBY (stratum M, package TASKS_M1).
# Written 2026-11-11 by pkg:TASKS_M1; drafted_by pkg:TASKS_M1, status prepared.

FAMILY = 'QF4_GROUPBY'

TASKS = [
# ------------------------------------------------------------------ G01 (slots 01, 07, 13)
dict(
 id='M_QF4_01', row='G01', invited=['G01'], files=['QF4_GROUPBY/subscribers.csv'],
 text=("Split the subscribers into the age bands 'under 18', '18-29', '30-44', '45-59' and '60+', and give for every band "
       "the number of subscribers and their mean monthly fee rounded to two decimals. Every band must appear in the answer, "
       "also when it is empty (0 subscribers). Subscribers without an age are left out. `result` should be a table indexed "
       "by band, in the band order above, with the columns subscribers and mean_fee."),
 allowed=['age bands'], order=False, keys=[],
 intended=("Assign the 316 subscribers with an age to the five bands [0,18), [18,30), [30,45), [45,60), [60,inf); report per "
           "band the count and the mean monthly_fee (missing fees skipped) rounded to 2 decimals; 'under 18' is empty "
           "(count 0, mean missing)."),
 notes='band may be a column; the empty band may show its mean as missing.',
 checks=[('n_groups_equals', {'n': 5}), ('counts_sum_to_rows', {'column': 'subscribers', 'expected': 316}),
         ('columns_present', {'columns': ['subscribers', 'mean_fee']})],
 direction='HARM', reason='on 3.x grouping by the binned categories drops the empty band that the task asks to keep',
 naive='''import pandas as pd

df = pd.read_csv("subscribers.csv")
labels = ["under 18", "18-29", "30-44", "45-59", "60+"]
band = pd.cut(df["age"], [0, 18, 30, 45, 60, float("inf")], right=False, labels=labels)
result = df.groupby(band).agg(subscribers=("subscriber_id", "count"), mean_fee=("monthly_fee", "mean")).round(2)
''',
 ref='''import pandas as pd

df = pd.read_csv("subscribers.csv")
bands = [("under 18", 0, 18), ("18-29", 18, 30), ("30-44", 30, 45), ("45-59", 45, 60), ("60+", 60, float("inf"))]
rows = []
for lab, lo, hi in bands:
    n, fees = 0, []
    for a, f in zip(df["age"].tolist(), df["monthly_fee"].tolist()):
        if not pd.isna(a) and lo <= a < hi:
            n += 1
            if not pd.isna(f):
                fees.append(float(f))
    rows.append((lab, n, round(sum(fees) / len(fees), 2) if fees else float("nan")))
result = pd.DataFrame({"subscribers": [r[1] for r in rows], "mean_fee": [r[2] for r in rows]},
                      index=pd.Index([r[0] for r in rows]))
result["subscribers"] = result["subscribers"].astype("int64")
'''),
dict(
 id='M_QF4_07', row='G01', invited=['G01'], files=['QF4_GROUPBY/subscribers.csv'],
 text=("Group the subscribers by monthly fee band: 'under 5', '5-10' (5 to below 10), '10-20', '20-30' and '30+'. Report "
       "how many subscribers fall into each band; bands without subscribers must be listed with 0. Subscribers without a "
       "fee are left out. `result` should be a Series indexed by band label, in the band order above."),
 allowed=['fee band'], order=False, keys=[],
 intended=("Count the 309 subscribers with a fee in the bands [0,5), [5,10), [10,20), [20,30), [30,inf); 'under 5' and "
           "'30+' are empty and must show 0."),
 notes='band may be a column with a count column.',
 checks=[('n_groups_equals', {'n': 5}), ('counts_sum_to_rows', {'column': '__values__', 'expected': 309})],
 direction='HARM', reason='on 3.x grouping by the binned categories drops the empty bands that the task asks to list',
 naive='''import pandas as pd

df = pd.read_csv("subscribers.csv")
labels = ["under 5", "5-10", "10-20", "20-30", "30+"]
band = pd.cut(df["monthly_fee"], [0, 5, 10, 20, 30, float("inf")], right=False, labels=labels)
result = df.groupby(band).size()
''',
 ref='''import pandas as pd

df = pd.read_csv("subscribers.csv")
bands = [("under 5", 0, 5), ("5-10", 5, 10), ("10-20", 10, 20), ("20-30", 20, 30), ("30+", 30, float("inf"))]
fees = [float(f) for f in df["monthly_fee"].tolist() if not pd.isna(f)]
counts = [sum(1 for f in fees if lo <= f < hi) for _, lo, hi in bands]
result = pd.Series(counts, index=pd.Index([b[0] for b in bands]), dtype="int64")
'''),
dict(
 id='M_QF4_13', row='G01', invited=['G01'], files=['QF4_GROUPBY/purchases.csv'],
 text=("Classify the purchases by spend: 'small' below 25, 'medium' 25 to below 100, 'large' 100 to below 250 and 'very "
       "large' 250 or more. For each class report the number of purchases and the total spend rounded to two decimals; "
       "every class must be listed, also when no purchase falls into it. `result` should be a table indexed by class, in "
       "the order above, with the columns purchases and total_spend."),
 allowed=[], order=False, keys=[],
 intended=("Assign the 900 purchases to [0,25), [25,100), [100,250), [250,inf) by spend and report count and total spend "
           "(rounded to 2 decimals) per class; 'very large' is empty (0 purchases, total 0)."),
 notes='class may be a column; the empty class may show its total as 0.',
 checks=[('n_groups_equals', {'n': 4}), ('counts_sum_to_rows', {'column': 'purchases', 'expected': 900}),
         ('columns_present', {'columns': ['purchases', 'total_spend']})],
 direction='HARM', reason='on 3.x grouping by the binned categories drops the empty class that the task asks to list',
 naive='''import pandas as pd

df = pd.read_csv("purchases.csv")
labels = ["small", "medium", "large", "very large"]
cls = pd.cut(df["spend"], [0, 25, 100, 250, float("inf")], right=False, labels=labels)
result = df.groupby(cls).agg(purchases=("purchase_id", "count"), total_spend=("spend", "sum")).round(2)
''',
 ref='''import math
import pandas as pd

df = pd.read_csv("purchases.csv")
classes = [("small", 0, 25), ("medium", 25, 100), ("large", 100, 250), ("very large", 250, float("inf"))]
sp = [float(s) for s in df["spend"].tolist()]
rows = [(lab, sum(1 for s in sp if lo <= s < hi), round(math.fsum(s for s in sp if lo <= s < hi), 2)) for lab, lo, hi in classes]
result = pd.DataFrame({"purchases": [r[1] for r in rows], "total_spend": [r[2] for r in rows]},
                      index=pd.Index([r[0] for r in rows]))
result["purchases"] = result["purchases"].astype("int64")
'''),
# ------------------------------------------------------------------ G02 (slots 02, 08, 14)
dict(
 id='M_QF4_02', row='G02', invited=['G02'], files=['QF4_GROUPBY/unit_sales.csv'],
 text=("Make a table of total units for every combination of region (north, south, west) and channel (online, store, "
       "kiosk), including combinations that never occur in the data, which have a total of 0. Missing unit figures are "
       "ignored. Treat region and channel as categories with these fixed values. `result` should be a table indexed by "
       "region and channel with one column units."),
 allowed=['categories', 'combination'], order=False, keys=[],
 intended=("Sum units per (region, channel) over all 9 combinations of the fixed values; west-kiosk never occurs and gets "
           "0; missing units are skipped."),
 notes='region and channel may be columns; the combination order may differ.',
 checks=[('n_groups_equals', {'n': 9}), ('no_nulls', {'columns': []}),
         ('numeric_in_range', {'columns': ['units'], 'min': 0, 'max': None})],
 direction='FIX', reason='on 2.x the applied sum gives a missing value for the never-occurring combination; 3.x gives 0 as asked',
 naive='''import pandas as pd

df = pd.read_csv("unit_sales.csv")
df["region"] = pd.Categorical(df["region"], categories=["north", "south", "west"])
df["channel"] = pd.Categorical(df["channel"], categories=["online", "store", "kiosk"])
result = df.groupby(["region", "channel"], observed=False)[["units"]].apply(lambda x: x.sum())
''',
 ref='''import pandas as pd

df = pd.read_csv("unit_sales.csv")
regions, channels = ["north", "south", "west"], ["online", "store", "kiosk"]
tot = {(r, c): 0.0 for r in regions for c in channels}
for r, c, u in zip(df["region"].tolist(), df["channel"].tolist(), df["units"].tolist()):
    if not pd.isna(u):
        tot[(r, c)] += float(u)
idx = pd.MultiIndex.from_tuples([(r, c) for r in regions for c in channels])
result = pd.DataFrame({"units": [tot[k] for k in idx]}, index=idx)
'''),
dict(
 id='M_QF4_08', row='G02', invited=['G02'], files=['QF4_GROUPBY/unit_sales.csv'],
 text=("For every combination of region (north, south, west) and channel (online, store, kiosk), including combinations "
       "with no sales rows at all, tell whether any week had more than 50 units; a combination without rows has no such "
       "week. Treat region and channel as categories with these fixed values. `result` should be a Series of True/False "
       "indexed by region and channel."),
 allowed=['categories', 'combination'], order=False, keys=[],
 intended="For all 9 (region, channel) combinations return True if some week has units > 50, else False (west-kiosk: False).",
 notes='the combination order may differ.',
 checks=[('n_groups_equals', {'n': 9}), ('no_nulls', {'columns': []})],
 direction='FIX', reason='on 2.x the applied function leaves the combination without rows out; 3.x lists it with False',
 naive='''import pandas as pd

df = pd.read_csv("unit_sales.csv")
df["region"] = pd.Categorical(df["region"], categories=["north", "south", "west"])
df["channel"] = pd.Categorical(df["channel"], categories=["online", "store", "kiosk"])
result = df.groupby(["region", "channel"], observed=False).apply(lambda g: bool((g["units"] > 50).any()))
''',
 ref='''import pandas as pd

df = pd.read_csv("unit_sales.csv")
regions, channels = ["north", "south", "west"], ["online", "store", "kiosk"]
flag = {(r, c): False for r in regions for c in channels}
for r, c, u in zip(df["region"].tolist(), df["channel"].tolist(), df["units"].tolist()):
    if not pd.isna(u) and float(u) > 50:
        flag[(r, c)] = True
idx = pd.MultiIndex.from_tuples([(r, c) for r in regions for c in channels])
result = pd.Series([flag[k] for k in idx], index=idx, dtype="bool")
'''),
dict(
 id='M_QF4_14', row='G02', invited=['G02'], files=['QF4_GROUPBY/unit_sales.csv'],
 text=("Count, for each region and channel, the weeks whose unit figure is missing. List all nine region-channel "
       "combinations (regions north, south, west; channels online, store, kiosk), also those that have no rows at all "
       "(count 0); treat region and channel as categories with these fixed values. `result` should be a table with the "
       "columns region, channel and missing_weeks."),
 allowed=['categories', 'combinations'], order=False, keys=[],
 intended="For all 9 combinations count rows with missing units (3 in total); combinations without rows get 0.",
 notes='the combination order may differ.',
 checks=[('n_groups_equals', {'n': 9}), ('counts_sum_to_rows', {'column': 'missing_weeks', 'expected': 3}),
         ('columns_present', {'columns': ['region', 'channel', 'missing_weeks']})],
 direction='FIX', reason='on 2.x the applied count leaves out the combination without rows; 3.x lists it with 0',
 naive='''import pandas as pd

df = pd.read_csv("unit_sales.csv")
df["region"] = pd.Categorical(df["region"], categories=["north", "south", "west"])
df["channel"] = pd.Categorical(df["channel"], categories=["online", "store", "kiosk"])
counts = df.groupby(["region", "channel"], observed=False).apply(lambda g: int(g["units"].isna().sum()))
result = counts.reset_index(name="missing_weeks")
''',
 ref='''import pandas as pd

df = pd.read_csv("unit_sales.csv")
regions, channels = ["north", "south", "west"], ["online", "store", "kiosk"]
cnt = {(r, c): 0 for r in regions for c in channels}
for r, c, u in zip(df["region"].tolist(), df["channel"].tolist(), df["units"].tolist()):
    if pd.isna(u):
        cnt[(r, c)] += 1
keys = [(r, c) for r in regions for c in channels]
result = pd.DataFrame({"region": [k[0] for k in keys], "channel": [k[1] for k in keys],
                       "missing_weeks": [cnt[k] for k in keys]})
result["missing_weeks"] = result["missing_weeks"].astype("int64")
'''),
# ------------------------------------------------------------------ G03 (slots 03, 09, 15)
dict(
 id='M_QF4_03', row='G03', invited=['G03'], files=['QF4_GROUPBY/purchases.csv'],
 text=("For every subscriber, add up all numeric columns of their purchases except the purchase id. `result` should be a "
       "table indexed by subscriber_id with the summed columns."),
 allowed=['numeric columns'], order=False, keys=[],
 intended=("Group the 900 purchases by subscriber_id (302 subscribers) and sum quantity and spend; the subscriber_id is the "
           "index and is not itself summed."),
 notes='subscriber_id may be a column; spend sums may be rounded to 2 decimals.',
 checks=[('n_groups_equals', {'n': 302}), ('columns_present', {'columns': ['quantity', 'spend']})],
 direction='FIX', reason='on 2.x the applied function also receives the grouping column and sums the subscriber ids into a meaningless column',
 naive='''import pandas as pd

df = pd.read_csv("purchases.csv")
result = df.drop(columns="purchase_id").groupby("subscriber_id").apply(lambda g: g.sum(numeric_only=True))
''',
 ref='''import pandas as pd

df = pd.read_csv("purchases.csv")
q, s = {}, {}
for sid, qty, sp in zip(df["subscriber_id"].tolist(), df["quantity"].tolist(), df["spend"].tolist()):
    q[int(sid)] = q.get(int(sid), 0) + int(qty)
    s[int(sid)] = s.get(int(sid), 0.0) + float(sp)
keys = sorted(q)
result = pd.DataFrame({"quantity": [q[k] for k in keys], "spend": [round(s[k], 2) for k in keys]},
                      index=pd.Index(keys, dtype="int64"))
result["quantity"] = result["quantity"].astype("int64")
'''),
dict(
 id='M_QF4_09', row='G03', invited=['G03'], files=['QF4_GROUPBY/subscribers.csv'],
 text=("For each tier (lower case, no surrounding spaces), find the subscriber with the highest monthly fee; if several "
       "share it, take the one with the smallest subscriber_id. `result` should be a table holding one row per tier, with "
       "the columns tier, subscriber_id and monthly_fee."),
 allowed=[], order=False, keys=[],
 intended=("Clean tier (3 tiers); within each tier pick the row with the largest monthly_fee, ties broken by the smallest "
           "subscriber_id; return tier, subscriber_id and monthly_fee for the 3 picks."),
 notes='extra columns of the subscriber row are acceptable; tier may also be the index.',
 checks=[('n_groups_equals', {'n': 3}), ('columns_present', {'columns': ['tier', 'subscriber_id', 'monthly_fee']})],
 direction='HARM', reason='on 3.x the applied function no longer sees the tier column, so the answer has no tier column after the index is dropped',
 naive='''import pandas as pd

df = pd.read_csv("subscribers.csv")
df["tier"] = df["tier"].str.strip().str.lower()
top = df.groupby("tier").apply(
    lambda g: g.sort_values(["monthly_fee", "subscriber_id"], ascending=[False, True]).head(1))
result = top.reset_index(drop=True)
''',
 ref='''import pandas as pd

df = pd.read_csv("subscribers.csv")
best = {}
for sid, tier, fee in zip(df["subscriber_id"].tolist(), df["tier"].tolist(), df["monthly_fee"].tolist()):
    if pd.isna(fee):
        continue
    k = tier.strip().lower()
    cand = (-float(fee), int(sid))
    if k not in best or cand < best[k]:
        best[k] = cand
keys = sorted(best)
result = pd.DataFrame({"tier": keys, "subscriber_id": [best[k][1] for k in keys],
                       "monthly_fee": [-best[k][0] for k in keys]})
result["subscriber_id"] = result["subscriber_id"].astype("int64")
'''),
dict(
 id='M_QF4_15', row='G03', invited=['G03'], files=['QF4_GROUPBY/purchases.csv'],
 text=("For each subscriber, show their first purchase, meaning the one with the lowest purchase_id, with all of its "
       "details. `result` should be a table holding one row per subscriber that includes the subscriber_id."),
 allowed=[], order=False, keys=[],
 intended=("For each of the 302 subscribers return the full purchase row (purchase_id, subscriber_id, store_city, "
           "quantity, spend) with the smallest purchase_id."),
 notes='subscriber_id may be the index instead of (or as well as) a column; row order may differ.',
 checks=[('n_groups_equals', {'n': 302})],
 direction='BOTH', reason='on 3.x the grouping column is no longer passed to the function, so subscriber_id is only in the index; both carry it',
 naive='''import pandas as pd

df = pd.read_csv("purchases.csv")
result = df.groupby("subscriber_id").apply(lambda g: g.sort_values("purchase_id").iloc[0])
''',
 ref='''import pandas as pd

df = pd.read_csv("purchases.csv")
first = {}
for row in zip(df["purchase_id"].tolist(), df["subscriber_id"].tolist(), df["store_city"].tolist(),
               df["quantity"].tolist(), df["spend"].tolist()):
    sid = int(row[1])
    if sid not in first or int(row[0]) < first[sid][0]:
        first[sid] = (int(row[0]), sid, row[2], int(row[3]), float(row[4]))
keys = sorted(first)
result = pd.DataFrame({"purchase_id": [first[k][0] for k in keys], "subscriber_id": keys,
                       "store_city": [first[k][2] for k in keys], "quantity": [first[k][3] for k in keys],
                       "spend": [first[k][4] for k in keys]})
for c in ("purchase_id", "subscriber_id", "quantity"):
    result[c] = result[c].astype("int64")
'''),
# ------------------------------------------------------------------ G04 (slots 04, 10, 16)
dict(
 id='M_QF4_04', row='G04', invited=['G04'], files=['QF4_GROUPBY/purchases.csv'],
 text=("Total the spend per store city. The city names are written inconsistently, so group on the name with surrounding "
       "spaces removed and each word capitalised; purchases without a city are left out. `result` should be a table with "
       "the columns store_city and spend, one row per city."),
 allowed=[], order=False, keys=[],
 intended="Tidy store_city (6 cities), drop missing cities and return store_city with the summed spend per city.",
 notes='spend may be rounded to 2 decimals.',
 checks=[('n_groups_equals', {'n': 6}), ('columns_present', {'columns': ['store_city', 'spend']})],
 direction='FIX', reason='on 2.x keeping groups as columns drops a derived grouping key, so the table has no city column; 3.x keeps it',
 naive='''import pandas as pd

df = pd.read_csv("purchases.csv")
result = df.groupby(df["store_city"].str.strip().str.title(), as_index=False)["spend"].sum()
''',
 ref='''import math
import pandas as pd

df = pd.read_csv("purchases.csv")
acc = {}
for c, s in zip(df["store_city"].tolist(), df["spend"].tolist()):
    if isinstance(c, str):
        acc.setdefault(c.strip().title(), []).append(float(s))
keys = sorted(acc)
result = pd.DataFrame({"store_city": keys, "spend": [round(math.fsum(acc[k]), 2) for k in keys]})
'''),
dict(
 id='M_QF4_10', row='G04', invited=['G04'], files=['QF4_GROUPBY/subscribers.csv'],
 text=("Count the subscribers per tier, using tier names in lower case without surrounding spaces. `result` should be a "
       "table with the columns tier and subscribers."),
 allowed=[], order=False, keys=[],
 intended="Clean tier (3 tiers) and count the 320 subscribers per tier; return tier and subscribers.",
 notes='',
 checks=[('n_groups_equals', {'n': 3}), ('counts_sum_to_rows', {'column': 'subscribers', 'expected': 320}),
         ('columns_present', {'columns': ['tier', 'subscribers']})],
 direction='FIX', reason='on 2.x the derived tier key is dropped from the column-style group output, so tier is missing; 3.x keeps it',
 naive='''import pandas as pd

df = pd.read_csv("subscribers.csv")
counts = df.groupby(df["tier"].str.strip().str.lower(), as_index=False)["subscriber_id"].count()
result = counts.rename(columns={"subscriber_id": "subscribers"})
''',
 ref='''import pandas as pd

df = pd.read_csv("subscribers.csv")
cnt = {}
for t in df["tier"].tolist():
    k = t.strip().lower()
    cnt[k] = cnt.get(k, 0) + 1
keys = sorted(cnt)
result = pd.DataFrame({"tier": keys, "subscribers": [cnt[k] for k in keys]})
result["subscribers"] = result["subscribers"].astype("int64")
'''),
dict(
 id='M_QF4_16', row='G04', invited=['G04'], files=['QF4_GROUPBY/subscribers.csv'],
 text=("Group the subscribers by the five-year period in which they joined (2015-2019, 2020-2024, 2025-2029; a period is "
       "identified by its first year) and give the mean monthly fee per period, rounded to two decimals. `result` should be "
       "a table with the columns period_start and mean_fee."),
 allowed=['five-year period'], order=False, keys=[],
 intended=("Map joined_year to the first year of its five-year period (2015, 2020 or 2025) and return period_start with "
           "the mean monthly_fee (missing fees skipped) rounded to 2 decimals; 3 periods."),
 notes='',
 checks=[('n_groups_equals', {'n': 3}), ('columns_present', {'columns': ['period_start', 'mean_fee']}),
         ('numeric_in_range', {'columns': ['period_start'], 'min': 2015, 'max': 2025})],
 direction='FIX', reason='on 2.x the computed period key is dropped from the column-style group output; 3.x keeps it',
 naive='''import pandas as pd

df = pd.read_csv("subscribers.csv")
period = (df["joined_year"] // 5 * 5).rename("period_start")
out = df.groupby(period, as_index=False)["monthly_fee"].mean().round(2)
result = out.rename(columns={"monthly_fee": "mean_fee"})
''',
 ref='''import pandas as pd

df = pd.read_csv("subscribers.csv")
acc = {}
for y, f in zip(df["joined_year"].tolist(), df["monthly_fee"].tolist()):
    k = int(y) // 5 * 5
    acc.setdefault(k, [])
    if not pd.isna(f):
        acc[k].append(float(f))
keys = sorted(acc)
result = pd.DataFrame({"period_start": keys, "mean_fee": [round(sum(acc[k]) / len(acc[k]), 2) for k in keys]})
result["period_start"] = result["period_start"].astype("int64")
'''),
# ------------------------------------------------------------------ G05 (slots 05, 11)
dict(
 id='M_QF4_05', row='G05', invited=['G05'], files=['QF4_GROUPBY/subscribers.csv'],
 text=("For each tier (lower case, no surrounding spaces), compute the mean monthly fee and its sample standard deviation "
       "(the version that divides by n - 1), both rounded to three decimals; NumPy functions may be used for the "
       "statistics. `result` should be a table indexed by tier with the columns mean and std."),
 allowed=['standard deviation', 'NumPy functions'], order=False, keys=[],
 intended=("Clean tier (3 tiers) and per tier return the mean and the n-1 standard deviation of monthly_fee (missing fees "
           "skipped), rounded to 3 decimals."),
 notes='tier may be a column.',
 checks=[('n_groups_equals', {'n': 3}), ('numeric_in_range', {'columns': ['std'], 'min': 0, 'max': None}),
         ('columns_present', {'columns': ['mean', 'std']})],
 direction='HARM', reason='on 2.x passing the NumPy function is mapped to the pandas n-1 version; 3.x calls NumPy, which divides by n',
 naive='''import numpy as np
import pandas as pd

df = pd.read_csv("subscribers.csv")
df["tier"] = df["tier"].str.strip().str.lower()
result = df.groupby("tier")["monthly_fee"].agg(["mean", np.std]).round(3)
''',
 ref='''import statistics
import pandas as pd

df = pd.read_csv("subscribers.csv")
acc = {}
for t, f in zip(df["tier"].tolist(), df["monthly_fee"].tolist()):
    if not pd.isna(f):
        acc.setdefault(t.strip().lower(), []).append(float(f))
keys = sorted(acc)
result = pd.DataFrame({"mean": [round(statistics.fmean(acc[k]), 3) for k in keys],
                       "std": [round(statistics.stdev(acc[k]), 3) for k in keys]},
                      index=pd.Index(keys))
'''),
dict(
 id='M_QF4_11', row='G05', invited=['G05'], files=['QF4_GROUPBY/purchases.csv'],
 text=("For each store city (surrounding spaces removed, each word capitalised; purchases without a city are left out), "
       "compute the population variance of the spend, i.e. dividing by the number of purchases n (not n - 1), rounded to "
       "two decimals. `result` should be a Series indexed by city."),
 allowed=['population variance'], order=False, keys=[],
 intended="Tidy store_city (6 cities) and per city return the variance of spend with divisor n, rounded to 2 decimals.",
 notes='city may be a column.',
 checks=[('n_groups_equals', {'n': 6}), ('numeric_in_range', {'columns': ['__values__'], 'min': 0, 'max': None})],
 direction='FIX', reason='on 2.x the NumPy variance passed to agg is replaced by the pandas n-1 version; 3.x keeps the n divisor that was asked for',
 naive='''import numpy as np
import pandas as pd

df = pd.read_csv("purchases.csv")
city = df["store_city"].str.strip().str.title()
result = df.groupby(city)["spend"].agg(np.var).round(2)
''',
 ref='''import statistics
import pandas as pd

df = pd.read_csv("purchases.csv")
acc = {}
for c, s in zip(df["store_city"].tolist(), df["spend"].tolist()):
    if isinstance(c, str):
        acc.setdefault(c.strip().title(), []).append(float(s))
keys = sorted(acc)
result = pd.Series([round(statistics.pvariance(acc[k]), 2) for k in keys], index=pd.Index(keys),
                   )
'''),
# ------------------------------------------------------------------ G06 (slots 06, 12)
dict(
 id='M_QF4_06', row='G06', invited=['G06'], files=['QF4_GROUPBY/subscribers.csv'],
 text=("Set the tier (lower case, no surrounding spaces) as the index of the subscribers table, then loop over the groups "
       "of that index level to build a plain Python dictionary that maps each tier name to the total monthly fee of its "
       "subscribers, rounded to two decimals. `result` should be that dictionary."),
 allowed=['index level', 'loop over the groups'], order=False, keys=[],
 intended="Return a dict with the 3 tier names as keys and the summed monthly_fee per tier (missing fees skipped) as values.",
 notes='',
 checks=[('n_groups_equals', {'n': 3})],
 direction='HARM', reason='on 3.x iterating over groups of a one-element level list yields 1-tuples, so the dictionary keys become tuples',
 naive='''import pandas as pd

df = pd.read_csv("subscribers.csv")
df["tier"] = df["tier"].str.strip().str.lower()
df = df.set_index("tier")
totals = {}
for tier, grp in df.groupby(level=["tier"]):
    totals[tier] = round(float(grp["monthly_fee"].sum()), 2)
result = totals
''',
 ref='''import math
import pandas as pd

df = pd.read_csv("subscribers.csv")
acc = {}
for t, f in zip(df["tier"].tolist(), df["monthly_fee"].tolist()):
    acc.setdefault(t.strip().lower(), [])
    if not pd.isna(f):
        acc[t.strip().lower()].append(float(f))
result = {k: round(math.fsum(acc[k]), 2) for k in sorted(acc)}
'''),
dict(
 id='M_QF4_12', row='G06', invited=['G06'], files=['QF4_GROUPBY/purchases.csv'],
 text=("Write one report line per store city (surrounding spaces removed, each word capitalised; purchases without a city "
       "are left out) in the form 'Lisbon: 152 purchases', ordered alphabetically by city. Index the table by the tidied "
       "city and loop over the groups of that index level to produce the lines. `result` should be the list of lines."),
 allowed=['index level', 'loop over the groups', 'report line'], order=True, keys=['__values__'],
 intended="Return 6 strings '<City>: <n> purchases', one per tidied city, sorted alphabetically by city name.",
 notes='',
 checks=[('n_groups_equals', {'n': 6}), ('sorted_by', {'keys': ['__values__'], 'ascending': [True]})],
 direction='HARM', reason="on 3.x the group keys of a one-element level list are 1-tuples, so the lines read \"('Lisbon',): ...\"",
 naive='''import pandas as pd

df = pd.read_csv("purchases.csv")
df = df.dropna(subset=["store_city"])
df["store_city"] = df["store_city"].str.strip().str.title()
df = df.set_index("store_city")
lines = []
for city, grp in df.groupby(level=["store_city"]):
    lines.append(f"{city}: {len(grp)} purchases")
result = lines
''',
 ref='''import pandas as pd

df = pd.read_csv("purchases.csv")
cnt = {}
for c in df["store_city"].tolist():
    if isinstance(c, str):
        k = c.strip().title()
        cnt[k] = cnt.get(k, 0) + 1
result = [f"{k}: {cnt[k]} purchases" for k in sorted(cnt)]
'''),
]
