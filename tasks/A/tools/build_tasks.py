"""Build tasks/A/<id>/{task.json, reference.py} for the stratum-A tasks (pkg:TASKS_RA, 2026-11-11).

drafted_by: pkg:TASKS_RA; status: prepared.
Task texts come from the frozen tools/intents_src.py (hash in tasks/A/INTENTS_FROZEN.sha256; the build aborts if it changed).
invited_ids_author were labelled by hand in step A2, after the intents were frozen (tasks are not rewritten for them).
Cards (flags, variants, property checks) are set from the task text alone. Property-check numbers are fixture facts of F-main
(row counts, number of distinct groups) computed here with the csv module; nothing here uses any run output.
Usage: python3 -I -B tasks/A/tools/build_tasks.py
"""
import csv, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.dirname(HERE)
S = os.path.abspath(os.path.join(A, '..', '..'))
sys.path.insert(0, HERE)
from intents_src import INTENTS  # noqa: E402

DRAFTED_BY = 'pkg:TASKS_RA'
STATUS = 'prepared'


def check_frozen():
    want = {}
    with open(os.path.join(A, 'INTENTS_FROZEN.sha256'), encoding='utf-8') as f:
        for ln in f:
            if ln.startswith('#') or not ln.strip():
                continue
            h, p = ln.split(None, 1)
            want[p.strip()] = h
    for p, h in want.items():
        got = hashlib.sha256(open(os.path.join(A, p), 'rb').read()).hexdigest()
        if got != h:
            sys.exit('frozen intents changed: %s' % p)


def descriptions():
    out = {}
    with open(os.path.join(S, 'fixtures', 'descriptions.tsv'), encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            out[r['path']] = r['description']
    return out


def rows(name):
    with open(os.path.join(S, 'fixtures', 'main', 'GEN', name), encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


# ---------------------------------------------------------------- fixture facts (F-main, csv module)
RID = rows('riders.csv')
TRP = rows('trips.csv')
STA = rows('stations.csv')
WEA = rows('weather_hourly.csv')
N_RIDERS, N_TRIPS, N_STATIONS, N_HOURS = len(RID), len(TRP), len(STA), len(WEA)
N_TRIP_RIDERS = len({r['rider_id'] for r in TRP})
N_JOINED = sum(1 for r in RID if r['joined_on'])
N_BIRTH = sum(1 for r in RID if r['birth_year'])
PAYMENTS = sorted({r['payment'].strip().lower() for r in TRP})
MEMBERSHIPS = sorted({r['membership'].strip().lower() for r in RID})
DISTRICTS = sorted({r['district'].strip().title() for r in STA})
N_DAYS_TRIPS = len({r['started_at'][:10] for r in TRP})
N_DAYS_WEATHER = len({r['observed_at'][:10] for r in WEA})
N_RATED = sum(1 for r in TRP if r['rating'])
YEARS_JOINED = sorted({int(r['joined_on'][:4]) for r in RID if r['joined_on']})
YEARS_OPENED = sorted({int(r['opened_on'][:4]) for r in STA})
N_BLOCKS = len({(r['observed_at'][:10], int(r['observed_at'][11:13]) // 6) for r in WEA})

GEN_CHECKS = [{'check': 'no_null_text', 'args': {}}, {'check': 'no_all_missing_column', 'args': {}}]


def pc(check, **args):
    return {'check': check, 'args': args}


VAR_NOTE_IDS = 'id columns (rider_id, station codes) may be written as integers without leading zeros'

# ---------------------------------------------------------------- cards and references
# Each entry: invited (A2, by hand), order_significant, sort_keys, intended, notes, checks, allowed words, reference source.
CARDS = {}

CARDS['A_TXT_01'] = dict(
 invited=['S05'], order=False, keys=[],
 intended="Read riders.csv and count the rows whose display_name contains at least one alphabetic character that is not one "
 "of the 26 basic Latin letters (in either case), such as an accented letter. The answer is one integer.",
 notes='a numpy integer or an int-valued float is the same count',
 checks=[pc('result_kind', kind='scalar'), pc('numeric_in_range', columns=['__values__'], min=0, max=N_RIDERS)],
 ref='''import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
names = [str(n) for n in riders['display_name'].tolist()]
result = int(sum(1 for n in names if any(ch.isalpha() and ord(ch) > 127 for ch in n)))
''')

CARDS['A_IMP_01'] = dict(
 invited=['C02'], order=False, keys=[],
 intended="Read trips.csv. For every trip with an empty duration_min, set duration_min to the median of the non-empty "
 "duration_min values of all trips with the same start_station; if that station has no non-empty duration, the value stays "
 "missing. All other columns and rows are unchanged; the result is the whole trips table (1500 rows).",
 notes=VAR_NOTE_IDS + '; duration_min may be float; started_at may be text or a timestamp',
 checks=[pc('n_groups_equals', n=N_TRIPS), pc('columns_present', columns=['trip_id', 'start_station', 'duration_min']),
         pc('numeric_in_range', columns=['duration_min'], min=0, max=None)],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str, 'start_station': str, 'end_station': str})
station_median = trips.groupby('start_station')['duration_min'].transform('median')
trips = trips.assign(duration_min=trips['duration_min'].where(trips['duration_min'].notna(), station_median))
result = trips
''')

CARDS['A_CONV_01'] = dict(
 invited=[], order=True, keys=['__index__'],
 intended="Read trips.csv keeping rider_id as text. Convert each trip's distance_km to metres (distance_km x 1000) rounded "
 "to the nearest whole metre, sum these per rider_id, and return a Series indexed by rider_id (text with leading zeros) "
 "sorted by rider_id ascending.",
 notes='the Series name is free',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_TRIP_RIDERS),
         pc('numeric_in_range', columns=['__values__'], min=0, max=None), pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str})
metres = (trips['distance_km'] * 1000).round().astype('int64')
result = metres.groupby(trips['rider_id']).sum().sort_index()
result.name = 'metres'
''')

CARDS['A_BIN_01'] = dict(
 invited=['G01'], order=False, keys=[],
 intended="Read trips.csv and put every trip into one of four bands by distance_km: < 2, 2 <= d < 5, 5 <= d < 10, d >= 10. "
 "For each band give the number of trips and the mean of the non-empty fares, rounded to 2 decimals; one row per band "
 "with columns band, n_trips, avg_fare.",
 notes='band labels may be spelled differently (e.g. interval notation); the band may be the index',
 checks=[pc('n_groups_equals', n=4), pc('counts_sum_to_rows', column='n_trips', expected=N_TRIPS),
         pc('numeric_in_range', columns=['avg_fare'], min=0, max=None)],
 ref='''import numpy as np
import pandas as pd

trips = pd.read_csv('trips.csv')
bands = ['under 2 km', '2 to under 5 km', '5 to under 10 km', '10 km or more']
d = trips['distance_km'].to_numpy()
band = np.select([d < 2, d < 5, d < 10], bands[:3], bands[3])
rows = []
for b in bands:
    sel = band == b
    fares = trips['fare'].to_numpy()[sel]
    fares = fares[~np.isnan(fares)]
    rows.append({'band': b, 'n_trips': int(sel.sum()), 'avg_fare': round(float(fares.sum() / len(fares)), 2)})
result = pd.DataFrame(rows)
''')

CARDS['A_DATE_01'] = dict(
 invited=[], order=True, keys=['year', 'quarter'],
 intended="Read riders.csv, parse joined_on as dates, drop riders with an empty joined_on, and count riders per (calendar "
 "year, quarter 1-4) of the join date. Return a table with columns year, quarter, n_riders sorted by year then quarter "
 "ascending; only quarters with at least one join appear.",
 notes='quarters without joins may be shown with 0',
 checks=[pc('counts_sum_to_rows', column='n_riders', expected=N_JOINED),
         pc('numeric_in_range', columns=['year'], min=YEARS_JOINED[0], max=YEARS_JOINED[-1]),
         pc('values_in_set', column='quarter', values=[1, 2, 3, 4]), pc('sorted_by', keys=['year', 'quarter'], ascending=[True, True])],
 ref='''import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
joined = pd.to_datetime(riders['joined_on'], format='%Y-%m-%d').dropna()
parts = pd.DataFrame({'year': joined.dt.year.astype('int64').to_numpy(),
                      'quarter': joined.dt.quarter.astype('int64').to_numpy()})
counts = parts.groupby(['year', 'quarter']).size()
result = pd.DataFrame({'year': [int(k[0]) for k in counts.index], 'quarter': [int(k[1]) for k in counts.index],
                       'n_riders': [int(v) for v in counts.to_numpy()]})
result = result.sort_values(['year', 'quarter'], kind='mergesort').reset_index(drop=True)
''')

CARDS['A_TS_01'] = dict(
 invited=[], order=False, keys=[],
 intended="Read weather_hourly.csv, take the calendar day of observed_at, and for each of the 30 days of September 2025 give "
 "the sum of rain_mm and the maximum of temp_c (empty temperatures ignored), indexed by the date.",
 notes='the date index may be dates, timestamps at midnight or YYYY-MM-DD text; rain_total may be rounded to 1 decimal',
 checks=[pc('n_groups_equals', n=N_DAYS_WEATHER), pc('date_year_in_range', columns=['__index__'], min_year=2025, max_year=2025),
         pc('numeric_in_range', columns=['rain_total'], min=0, max=None), pc('no_nulls', columns=['temp_max'])],
 ref='''import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
day = pd.to_datetime(weather['observed_at'], format='%Y-%m-%d %H:%M').dt.normalize()
tenths = (weather['rain_mm'] * 10).round().astype('int64')
frame = pd.DataFrame({'day': day, 'tenths': tenths, 'temp_c': weather['temp_c']})
g = frame.groupby('day').agg(rain_tenths=('tenths', 'sum'), temp_max=('temp_c', 'max'))
result = pd.DataFrame({'rain_total': g['rain_tenths'].to_numpy() / 10, 'temp_max': g['temp_max'].to_numpy()},
                      index=pd.Index(g.index, name='date'))
''')

CARDS['A_TOP_01'] = dict(
 invited=['R03', 'G07'], order=True, keys=['total_km'],
 intended="Read trips.csv, sum distance_km per rider_id, and return the 5 riders with the largest sums as a table with "
 "columns rider_id and total_km (rounded to 2 decimals), ordered from the largest total to the smallest.",
 notes=VAR_NOTE_IDS + '; rider_id may be the index',
 checks=[pc('n_groups_equals', n=5), pc('sorted_by', keys=['total_km'], ascending=[False]),
         pc('numeric_in_range', columns=['total_km'], min=0, max=None)],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str})
cents = (trips['distance_km'] * 100).round().astype('int64')
per_rider = cents.groupby(trips['rider_id']).sum()
table = pd.DataFrame({'rider_id': [str(k) for k in per_rider.index], 'cents': [int(v) for v in per_rider.to_numpy()]})
table = table.sort_values(['cents', 'rider_id'], ascending=[False, True], kind='mergesort').head(5)
result = pd.DataFrame({'rider_id': table['rider_id'].tolist(), 'total_km': [round(c / 100, 2) for c in table['cents']]})
''')

CARDS['A_MRG_01'] = dict(
 invited=[], order=False, keys=[],
 intended="Read trips.csv and stations.csv, normalise stations.district (strip spaces, title case), attach to every trip the "
 "district of the station whose station_code equals the trip's start_station, and count trips per district; a Series "
 "indexed by district.",
 notes='district labels may differ in letter case; the counts may be a one-column table',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=len(DISTRICTS)),
         pc('counts_sum_to_rows', column='__values__', expected=N_TRIPS)],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str, 'start_station': str, 'end_station': str})
stations = pd.read_csv('stations.csv', dtype={'station_code': str})
district_of = {str(c): str(d).strip().title() for c, d in zip(stations['station_code'], stations['district'])}
districts = pd.Series([district_of.get(str(s)) for s in trips['start_station']], name='district')
counts = districts.groupby(districts).size().sort_index()
result = pd.Series([int(v) for v in counts.to_numpy()], index=pd.Index([str(k) for k in counts.index], name='district'),
                   name='count')
''')

CARDS['A_PIV_01'] = dict(
 invited=['R06'], order=False, keys=[],
 intended="Read trips.csv, drop trips with an empty rating, normalise payment (strip, lower case), and count trips for each "
 "payment (rows) and rating 1-5 (columns), with 0 for empty combinations.",
 notes='rating column labels may be 1.0-5.0; row and column order free',
 checks=[pc('n_groups_equals', n=len(PAYMENTS)), pc('no_nulls', columns=[]), pc('numeric_in_range', columns=[], min=0, max=N_RATED)],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv')
rated = trips[trips['rating'].notna()]
payment = [str(p).strip().lower() for p in rated['payment']]
rating = [int(r) for r in rated['rating']]
pays = sorted(set(payment))
counts = {(p, r): 0 for p in pays for r in range(1, 6)}
for p, r in zip(payment, rating):
    counts[(p, r)] += 1
result = pd.DataFrame([[counts[(p, r)] for r in range(1, 6)] for p in pays],
                      index=pd.Index(pays, name='payment'), columns=pd.Index(list(range(1, 6)), name='rating'))
''')

CARDS['A_ENC_01'] = dict(
 invited=[], order=False, keys=[],
 intended="Read riders.csv, normalise home_district (strip, title case), and for every rider compute the share of all 400 "
 "riders whose normalised district equals theirs; return rider_id and district_share (one row per rider).",
 notes=VAR_NOTE_IDS + '; rider_id may be the index',
 checks=[pc('n_groups_equals', n=N_RIDERS), pc('rate_in_unit_interval', columns=['district_share']),
         pc('no_nulls', columns=['district_share'])],
 ref='''import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
district = [str(d).strip().title() for d in riders['home_district']]
n = len(district)
count = {}
for d in district:
    count[d] = count.get(d, 0) + 1
result = pd.DataFrame({'rider_id': riders['rider_id'], 'district_share': [count[d] / n for d in district]})
''')

CARDS['A_UPD_01'] = dict(
 invited=['C01'], order=False, keys=[],
 intended="Read trips.csv; for every trip with duration_min > 60 add 2.00 to fare (an empty fare stays empty; an empty "
 "duration is not > 60); all other values unchanged; return the whole trips table.",
 notes=VAR_NOTE_IDS,
 checks=[pc('n_groups_equals', n=N_TRIPS), pc('columns_present', columns=['trip_id', 'duration_min', 'fare']),
         pc('numeric_in_range', columns=['fare'], min=0, max=None)],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str, 'start_station': str, 'end_station': str})
long_trip = (trips['duration_min'] > 60).to_numpy()
fare = trips['fare'].to_numpy().copy()
fare[long_trip] = fare[long_trip] + 2.0
result = trips.assign(fare=fare)
''')

CARDS['A_RPT_01'] = dict(
 invited=['G07'], order=False, keys=[],
 intended="Read trips.csv, normalise payment (strip, lower case) and per payment method give: n_trips (row count), "
 "total_fare (sum of non-empty fares), mean_km (mean distance_km) and rated_share (share of trips with a non-empty "
 "rating), each rounded to 2 decimals; indexed by payment method.",
 notes='payment may be a column instead of the index',
 checks=[pc('n_groups_equals', n=len(PAYMENTS)), pc('counts_sum_to_rows', column='n_trips', expected=N_TRIPS),
         pc('rate_in_unit_interval', columns=['rated_share']), pc('numeric_in_range', columns=['total_fare', 'mean_km'], min=0, max=None)],
 ref='''import numpy as np
import pandas as pd

trips = pd.read_csv('trips.csv')
payment = np.array([str(p).strip().lower() for p in trips['payment']], dtype=object)
fare = trips['fare'].to_numpy()
km = trips['distance_km'].to_numpy()
rated = trips['rating'].notna().to_numpy()
rows = []
for p in sorted(set(payment)):
    sel = payment == p
    f = fare[sel]
    f = f[~np.isnan(f)]
    rows.append({'payment': p, 'n_trips': int(sel.sum()),
                 'total_fare': round(int(np.round(f * 100).astype('int64').sum()) / 100, 2),
                 'mean_km': round(int(np.round(km[sel] * 100).astype('int64').sum()) / 100 / int(sel.sum()), 2),
                 'rated_share': round(int(rated[sel].sum()) / int(sel.sum()), 2)})
result = pd.DataFrame(rows).set_index('payment')
''')

CARDS['A_TXT_02'] = dict(
 invited=[], order=False, keys=[],
 intended="Read stations.csv; split each station_name at its last space into base_name (the text before it) and side (the "
 "last word); return station_code, base_name, side, one row per station.",
 notes=VAR_NOTE_IDS,
 checks=[pc('n_groups_equals', n=N_STATIONS), pc('values_in_set', column='side', values=['North', 'South', 'East']),
         pc('no_nulls', columns=['base_name', 'side'])],
 ref='''import pandas as pd

stations = pd.read_csv('stations.csv', dtype={'station_code': str})
parts = [str(n).strip().rsplit(' ', 1) for n in stations['station_name']]
result = pd.DataFrame({'station_code': [str(c) for c in stations['station_code']],
                       'base_name': [p[0] for p in parts], 'side': [p[1] for p in parts]})
''')

CARDS['A_IMP_02'] = dict(
 invited=['C02', 'G07'], order=False, keys=[],
 intended="Read weather_hourly.csv; for each hour of the day (0-23) compute the mean of the non-empty temp_c values over "
 "the month, rounded to 1 decimal; replace each empty temp_c by the value for its hour; return all 720 temperatures as a "
 "Series indexed by observed_at.",
 notes='the index may be the timestamp text or parsed timestamps; values that were present stay as they are',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_HOURS), pc('no_nulls', columns=[]),
         pc('numeric_in_range', columns=['__values__'], min=-10, max=40)],
 ref='''import numpy as np
import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
when = pd.to_datetime(weather['observed_at'], format='%Y-%m-%d %H:%M')
hour = when.dt.hour.astype('int64').to_numpy()
temp = weather['temp_c'].to_numpy()
fill = {}
for h in range(24):
    v = temp[(hour == h) & ~np.isnan(temp)]
    tenths = np.round(v * 10).astype('int64')
    fill[h] = float(np.round(int(tenths.sum()) / len(tenths))) / 10
filled = [fill[h] if np.isnan(t) else float(t) for h, t in zip(hour, temp)]
result = pd.Series(filled, index=pd.DatetimeIndex(when, name='observed_at'), name='temp_c')
''')

CARDS['A_CONV_02'] = dict(
 invited=['C02'], order=False, keys=[],
 intended="Read riders.csv; treat an empty credit_balance as 0; convert each balance to whole cents (x 100, rounded to an "
 "integer); normalise membership (strip, lower case); return the total cents per membership type as a Series indexed by "
 "membership type.",
 notes='the totals may be integer-valued floats',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=len(MEMBERSHIPS))],
 ref='''import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
cents = (riders['credit_balance'].fillna(0.0) * 100).round().astype('int64').to_numpy()
membership = [str(m).strip().lower() for m in riders['membership']]
total = {}
for m, c in zip(membership, cents):
    total[m] = total.get(m, 0) + int(c)
keys = sorted(total)
result = pd.Series([total[k] for k in keys], index=pd.Index(keys, name='membership'), name='cents', dtype='int64')
''')

CARDS['A_BIN_02'] = dict(
 invited=['G01', 'G02'], order=False, keys=[],
 intended="Read riders.csv, drop riders with an empty birth_year, set age = 2025 - birth_year, assign groups under 25 (age "
 "< 25), 25-39, 40-59 and 60 or older (age >= 60), normalise membership (strip, lower case), and count riders per age "
 "group (rows) and membership type (columns), 0 where none.",
 notes='group labels may be spelled differently; row and column order free',
 checks=[pc('n_groups_equals', n=4), pc('no_nulls', columns=[]), pc('numeric_in_range', columns=[], min=0, max=N_BIRTH)],
 ref='''import numpy as np
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
known = riders[riders['birth_year'].notna()]
age = 2025 - known['birth_year'].to_numpy().astype('int64')
labels = ['under 25', '25-39', '40-59', '60 or older']
group = np.select([age < 25, age < 40, age < 60], labels[:3], labels[3])
membership = [str(m).strip().lower() for m in known['membership']]
types = sorted(set(membership))
counts = {(g, m): 0 for g in labels for m in types}
for g, m in zip(group, membership):
    counts[(str(g), m)] += 1
result = pd.DataFrame([[counts[(g, m)] for m in types] for g in labels],
                      index=pd.Index(labels, name='age_group'), columns=pd.Index(types, name='membership'))
''')

CARDS['A_DATE_02'] = dict(
 invited=['D02'], order=False, keys=[],
 intended="Read trips.csv, drop trips with an empty duration_min, compute end = started_at + duration_min minutes, and count "
 "trips whose end falls on a later calendar date than started_at. One integer.",
 notes='a numpy integer is the same count',
 checks=[pc('result_kind', kind='scalar'), pc('numeric_in_range', columns=['__values__'], min=0, max=N_TRIPS)],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv')
known = trips[trips['duration_min'].notna()]
clock = [str(s)[11:16] for s in known['started_at']]
minute_of_day = [int(c[:2]) * 60 + int(c[3:5]) for c in clock]
result = int(sum(1 for m, d in zip(minute_of_day, known['duration_min'].tolist()) if m + int(d) >= 1440))
''')

CARDS['A_TS_02'] = dict(
 invited=['D04'], order=False, keys=[],
 intended="Read trips.csv, count trips per calendar day of started_at, fill every day between the first and last trip day "
 "that has no trips with 0, and take the 7-day rolling mean (window of the current and 6 previous days) of the daily "
 "counts; a Series indexed by day.",
 notes='the first 6 values may be empty (full window) or partial-window means; the day index may be dates or text',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_DAYS_TRIPS),
         pc('date_year_in_range', columns=['__index__'], min_year=2025, max_year=2025),
         pc('numeric_in_range', columns=['__values__'], min=0, max=None)],
 ref='''import numpy as np
import pandas as pd

trips = pd.read_csv('trips.csv')
day = pd.to_datetime(trips['started_at'], format='%Y-%m-%d %H:%M').dt.normalize()
per_day = day.groupby(day).size()
days = pd.date_range(per_day.index.min(), per_day.index.max(), freq='D', name='day')
counts = np.array([int(per_day.get(d, 0)) for d in days], dtype='int64')
cum = np.concatenate([[0], np.cumsum(counts)])
values = [np.nan] * 6 + [(int(cum[i + 1]) - int(cum[i - 6])) / 7 for i in range(6, len(counts))]
result = pd.Series(values, index=days, name='rolling_mean_7d')
''')

CARDS['A_TOP_02'] = dict(
 invited=['R03', 'G03'], order=True, keys=['payment', 'duration_min'],
 intended="Read trips.csv, normalise payment (strip, lower case), ignore trips with an empty duration_min, and for each "
 "payment method keep the 3 trips with the largest duration_min (ties broken by smaller trip_id); return payment, "
 "trip_id, duration_min sorted by payment ascending and duration_min descending.",
 notes='duration_min may be float',
 checks=[pc('n_groups_equals', n=3 * len(PAYMENTS)), pc('values_in_set', column='payment', values=PAYMENTS),
         pc('sorted_by', keys=['payment', 'duration_min'], ascending=[True, False])],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv')
known = trips[trips['duration_min'].notna()]
table = pd.DataFrame({'payment': [str(p).strip().lower() for p in known['payment']],
                      'trip_id': known['trip_id'].astype('int64').to_numpy(),
                      'duration_min': known['duration_min'].astype('int64').to_numpy()})
table = table.sort_values(['payment', 'duration_min', 'trip_id'], ascending=[True, False, True], kind='mergesort')
parts = [g.head(3) for _, g in table.groupby('payment', sort=True)]
result = pd.concat(parts, ignore_index=True)[['payment', 'trip_id', 'duration_min']]
''')

CARDS['A_MRG_02'] = dict(
 invited=['G07'], order=False, keys=[],
 intended="Read trips.csv and riders.csv (rider_id as the key), normalise riders.membership (strip, lower case), attach "
 "each trip's membership, and give the mean of the non-empty fares per membership type, rounded to 2 decimals; a Series "
 "indexed by membership type.",
 notes='may be a one-column table',
 checks=[pc('n_groups_equals', n=len(MEMBERSHIPS)), pc('numeric_in_range', columns=['__values__'], min=0, max=None)],
 ref='''import numpy as np
import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'rider_id': str})
riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
member_of = {str(r): str(m).strip().lower() for r, m in zip(riders['rider_id'], riders['membership'])}
fare = trips['fare'].to_numpy()
total, count = {}, {}
for r, f in zip(trips['rider_id'], fare):
    if np.isnan(f):
        continue
    m = member_of[str(r)]
    total[m] = total.get(m, 0) + int(round(f * 100))
    count[m] = count.get(m, 0) + 1
keys = sorted(total)
result = pd.Series([round(total[k] / count[k] / 100, 2) for k in keys], index=pd.Index(keys, name='membership'),
                   name='avg_fare')
''')

CARDS['A_PIV_02'] = dict(
 invited=['R06'], order=False, keys=[],
 intended="Read weather_hourly.csv, normalise sky (strip, lower case), and for each day of the month (rows 1-30) and sky "
 "condition (columns) give the mean of the non-empty temp_c values of the matching hours, rounded to 1 decimal; a cell "
 "is empty when that sky condition did not occur on that day (or only at hours with an empty temperature).",
 notes='row and column order free',
 checks=[pc('n_groups_equals', n=N_DAYS_WEATHER), pc('numeric_in_range', columns=[], min=-10, max=40)],
 ref='''import numpy as np
import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
day = [int(str(t)[8:10]) for t in weather['observed_at']]
sky = [str(s).strip().lower() for s in weather['sky']]
temp = weather['temp_c'].to_numpy()
skies = sorted(set(sky))
days = sorted(set(day))
tot, cnt = {}, {}
for d, s, t in zip(day, sky, temp):
    if np.isnan(t):
        continue
    tot[(d, s)] = tot.get((d, s), 0) + int(round(t * 10))
    cnt[(d, s)] = cnt.get((d, s), 0) + 1
cells = [[float(np.round(tot[(d, s)] / cnt[(d, s)])) / 10 if (d, s) in cnt else np.nan for s in skies] for d in days]
result = pd.DataFrame(cells, index=pd.Index(days, name='day'), columns=pd.Index(skies, name='sky'))
''')

CARDS['A_ENC_02'] = dict(
 invited=[], order=False, keys=[],
 intended="Read trips.csv, normalise payment (strip, lower case), rank the methods by number of trips (most frequent = 0, "
 "next = 1, ...), and return each trip's code as a Series indexed by trip_id.",
 notes='index may be the default index if the order of trips.csv is kept',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_TRIPS),
         pc('values_in_set', column='__values__', values=list(range(len(PAYMENTS))))],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv')
payment = [str(p).strip().lower() for p in trips['payment']]
freq = {}
for p in payment:
    freq[p] = freq.get(p, 0) + 1
order = sorted(freq, key=lambda k: (-freq[k], k))
code = {k: i for i, k in enumerate(order)}
result = pd.Series([code[p] for p in payment], index=pd.Index(trips['trip_id'].astype('int64').to_numpy(), name='trip_id'),
                   name='payment_code', dtype='int64')
''')

CARDS['A_UPD_02'] = dict(
 invited=['C01'], order=False, keys=[],
 intended="Read riders.csv; in_debt = credit_balance < 0 (False for an empty balance); set negative balances to 0, empty "
 "balances stay empty; return rider_id, credit_balance, in_debt for every rider.",
 notes=VAR_NOTE_IDS + '; in_debt may be 0/1',
 checks=[pc('n_groups_equals', n=N_RIDERS), pc('numeric_in_range', columns=['credit_balance'], min=0, max=None),
         pc('no_nulls', columns=['in_debt'])],
 ref='''import numpy as np
import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
bal = riders['credit_balance'].to_numpy()
neg = np.where(np.isnan(bal), False, bal < 0)
result = pd.DataFrame({'rider_id': riders['rider_id'], 'credit_balance': np.where(neg, 0.0, bal),
                       'in_debt': neg.astype(bool)})
''')

CARDS['A_RPT_02'] = dict(
 invited=[], order=True, keys=['net_flow'],
 intended="Read trips.csv and stations.csv (codes as text); for every station in stations.csv count trips with that "
 "start_station (starts) and with that end_station (ends), net_flow = ends - starts, 0 counts for stations without trips; "
 "indexed by station_code, sorted by net_flow descending (ties in any order).",
 notes=VAR_NOTE_IDS + '; station_code may be a column',
 checks=[pc('n_groups_equals', n=N_STATIONS), pc('counts_sum_to_rows', column='starts', expected=N_TRIPS),
         pc('counts_sum_to_rows', column='ends', expected=N_TRIPS), pc('sorted_by', keys=['net_flow'], ascending=[False])],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'start_station': str, 'end_station': str})
stations = pd.read_csv('stations.csv', dtype={'station_code': str})
codes = [str(c) for c in stations['station_code']]
starts, ends = dict.fromkeys(codes, 0), dict.fromkeys(codes, 0)
for s in trips['start_station']:
    if str(s) in starts:
        starts[str(s)] += 1
for e in trips['end_station']:
    if str(e) in ends:
        ends[str(e)] += 1
rows = [(c, starts[c], ends[c], ends[c] - starts[c]) for c in codes]
rows.sort(key=lambda r: -r[3])
result = pd.DataFrame({'starts': [r[1] for r in rows], 'ends': [r[2] for r in rows], 'net_flow': [r[3] for r in rows]},
                      index=pd.Index([r[0] for r in rows], name='station_code'))
''')

CARDS['A_TXT_03'] = dict(
 invited=[], order=False, keys=[],
 intended="Read riders.csv (rider_id as text); for every rider take the last word of the stripped display_name, its first "
 "three letters in upper case, followed by the last four characters of rider_id; a Series indexed by rider_id.",
 notes='the index may be the default index with rider_id as a column',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_RIDERS), pc('no_nulls', columns=[])],
 ref='''import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
codes = [str(n).strip().split()[-1][:3].upper() + str(r)[-4:] for n, r in zip(riders['display_name'], riders['rider_id'])]
result = pd.Series(codes, index=pd.Index([str(r) for r in riders['rider_id']], name='rider_id'), name='code')
''')

CARDS['A_IMP_03'] = dict(
 invited=['C02'], order=False, keys=[],
 intended="Read riders.csv, normalise home_district (strip, title case); for each district find the most frequent "
 "non-empty birth_year (smallest year among ties); replace each empty birth_year by its district's value; return "
 "rider_id, home_district (normalised) and birth_year for every rider.",
 notes=VAR_NOTE_IDS + '; home_district may be the original text; birth_year may be float',
 checks=[pc('n_groups_equals', n=N_RIDERS), pc('no_nulls', columns=['birth_year']),
         pc('numeric_in_range', columns=['birth_year'], min=1900, max=2025)],
 ref='''import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
district = [str(d).strip().title() for d in riders['home_district']]
years = riders['birth_year'].tolist()
freq = {}
for d, y in zip(district, years):
    if y == y:
        freq.setdefault(d, {})
        freq[d][int(y)] = freq[d].get(int(y), 0) + 1
mode = {d: min(c, key=lambda y: (-c[y], y)) for d, c in freq.items()}
filled = [int(y) if y == y else mode[d] for d, y in zip(district, years)]
result = pd.DataFrame({'rider_id': riders['rider_id'], 'home_district': district,
                       'birth_year': pd.Series(filled, dtype='int64')})
''')

CARDS['A_CONV_03'] = dict(
 invited=['S03'], order=False, keys=[],
 intended="Read trips.csv; for each trip the text '€' followed by the fare with exactly two decimals, or 'n/a' when the fare "
 "is empty; a Series indexed by trip_id.",
 notes='',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_TRIPS), pc('no_nulls', columns=[])],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv')
labels = ['n/a' if f != f else '\\u20ac%.2f' % f for f in trips['fare'].tolist()]
result = pd.Series(labels, index=pd.Index(trips['trip_id'].astype('int64').to_numpy(), name='trip_id'), name='fare_label')
''')

CARDS['A_BIN_03'] = dict(
 invited=['G01'], order=False, keys=[],
 intended="Read weather_hourly.csv, classify wind_kmh as calm (0-5), breeze (6-20), windy (21-35) or strong (>= 36), and per "
 "class give the number of hours and the sum of rain_mm rounded to 1 decimal; indexed by class.",
 notes='classes with no hours may be shown with 0 or left out; class order free',
 checks=[pc('counts_sum_to_rows', column='hours', expected=N_HOURS), pc('numeric_in_range', columns=['rain_total'], min=0, max=None)],
 ref='''import numpy as np
import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
wind = weather['wind_kmh'].to_numpy()
label = np.select([wind <= 5, wind <= 20, wind <= 35], ['calm', 'breeze', 'windy'], 'strong')
tenths = np.round(weather['rain_mm'].to_numpy() * 10).astype('int64')
classes = ['calm', 'breeze', 'windy', 'strong']
result = pd.DataFrame({'hours': [int((label == c).sum()) for c in classes],
                       'rain_total': [int(tenths[label == c].sum()) / 10 for c in classes]},
                      index=pd.Index(classes, name='class'))
''')

CARDS['A_DATE_03'] = dict(
 invited=[], order=False, keys=[],
 intended="Read stations.csv, parse opened_on as a date, and give for every station its station_code, the year of "
 "opened_on and the number of days from opened_on to 2025-12-31.",
 notes=VAR_NOTE_IDS,
 checks=[pc('n_groups_equals', n=N_STATIONS), pc('numeric_in_range', columns=['opened_year'], min=YEARS_OPENED[0], max=YEARS_OPENED[-1]),
         pc('numeric_in_range', columns=['days_open'], min=0, max=None)],
 ref='''import datetime as dt
import pandas as pd

stations = pd.read_csv('stations.csv', dtype={'station_code': str})
opened = [dt.date.fromisoformat(str(d)) for d in stations['opened_on']]
end = dt.date(2025, 12, 31)
result = pd.DataFrame({'station_code': [str(c) for c in stations['station_code']],
                       'opened_year': pd.Series([d.year for d in opened], dtype='int64'),
                       'days_open': pd.Series([(end - d).days for d in opened], dtype='int64')})
''')

CARDS['A_TS_03'] = dict(
 invited=[], order=False, keys=[],
 intended="Read weather_hourly.csv, assign each hour to the 6-hour block starting at 00:00, 06:00, 12:00 or 18:00 of its "
 "day, and give per block the mean of the non-empty temp_c and the mean wind_kmh, each rounded to 2 decimals; indexed by "
 "the block start.",
 notes='the block start may be a timestamp or text',
 checks=[pc('n_groups_equals', n=N_BLOCKS), pc('date_year_in_range', columns=['__index__'], min_year=2025, max_year=2025),
         pc('numeric_in_range', columns=['wind_kmh'], min=0, max=None)],
 ref='''import numpy as np
import pandas as pd

weather = pd.read_csv('weather_hourly.csv')
stamps = [str(t) for t in weather['observed_at']]
block = ['%s %02d:00' % (s[:10], (int(s[11:13]) // 6) * 6) for s in stamps]
temp = weather['temp_c'].to_numpy()
wind = weather['wind_kmh'].to_numpy().astype('int64')
keys = sorted(set(block))
t_sum, t_cnt, w_sum, w_cnt = {}, {}, {}, {}
for b, t, w in zip(block, temp, wind):
    w_sum[b] = w_sum.get(b, 0) + int(w)
    w_cnt[b] = w_cnt.get(b, 0) + 1
    if not np.isnan(t):
        t_sum[b] = t_sum.get(b, 0) + int(round(t * 10))
        t_cnt[b] = t_cnt.get(b, 0) + 1
result = pd.DataFrame({'temp_c': [round(t_sum[k] / t_cnt[k] / 10, 2) if k in t_cnt else np.nan for k in keys],
                       'wind_kmh': [round(w_sum[k] / w_cnt[k], 2) for k in keys]},
                      index=pd.DatetimeIndex(pd.to_datetime(keys, format='%Y-%m-%d %H:%M'), name='block_start'))
''')

CARDS['A_TOP_03'] = dict(
 invited=['R03'], order=True, keys=['credit_balance'],
 intended="Read riders.csv (rider_id as text), ignore empty credit_balance, sort by credit_balance descending with ties by "
 "rider_id ascending, keep the first 10, and return rider_id, display_name (leading and trailing spaces removed) and "
 "credit_balance in that order.",
 notes=VAR_NOTE_IDS,
 checks=[pc('n_groups_equals', n=10), pc('sorted_by', keys=['credit_balance'], ascending=[False]),
         pc('no_nulls', columns=['credit_balance'])],
 ref='''import pandas as pd

riders = pd.read_csv('riders.csv', dtype={'rider_id': str})
known = riders[riders['credit_balance'].notna()]
rows = sorted(zip(known['rider_id'], known['display_name'], known['credit_balance']), key=lambda r: (-float(r[2]), str(r[0])))[:10]
result = pd.DataFrame({'rider_id': [str(r[0]) for r in rows], 'display_name': [str(r[1]).strip() for r in rows],
                       'credit_balance': [float(r[2]) for r in rows]})
''')

CARDS['A_MRG_03'] = dict(
 invited=[], order=False, keys=[],
 intended="Read trips.csv and fare_changes.csv (station codes as text), drop fare changes with an empty new_base_fare, match "
 "each trip's start_station to a fare change's station_code, and count matched trips per new_base_fare value; a Series "
 "indexed by new_base_fare.",
 notes='new_base_fare labels may be text such as 1.50; fare values without trips may be shown with 0',
 checks=[pc('result_kind', kind='series'), pc('numeric_in_range', columns=['__values__'], min=0, max=N_TRIPS)],
 ref='''import pandas as pd

trips = pd.read_csv('trips.csv', dtype={'start_station': str})
changes = pd.read_csv('fare_changes.csv', dtype={'station_code': str})
fare_of = {str(c): float(f) for c, f in zip(changes['station_code'], changes['new_base_fare']) if f == f}
count = {}
for s in trips['start_station']:
    f = fare_of.get(str(s))
    if f is not None:
        count[f] = count.get(f, 0) + 1
keys = sorted(count)
result = pd.Series([count[k] for k in keys], index=pd.Index(keys, name='new_base_fare'), name='n_trips', dtype='int64')
''')


def build():
    check_frozen()
    desc = descriptions()
    assert list(CARDS) == list(INTENTS), 'cards and intents differ'
    for tid, (files, text) in INTENTS.items():
        c = CARDS[tid]
        task = {
            'id': tid, 'stratum': 'A', 'family': None, 'generic_family': tid.split('_')[1], 'catalogue_row': None,
            'files': [{'path': 'GEN/' + f, 'description': desc['GEN/' + f]} for f in files],
            'task_text': text, 'allowed_task_words': [], 'invited_ids_author': c['invited'],
            'order_significant': c['order'], 'sort_keys': c['keys'], 'dtype_significant': False,
            'intended_computation': c['intended'],
            'acceptable_variants': {'row_order': 'ties_only' if c['order'] else 'any', 'label_spelling': True,
                                    'missing_value_representation': True, 'rounding_sig_digits': 6, 'notes': c['notes']},
            'property_checks': GEN_CHECKS + c['checks'],
            'predicted_direction': None, 'naive_path': None, 'reference_path': 'reference.py',
            'so_question_id': None, 'so_url': None, 'so_creation_date': None, 'so_score': None, 'so_licence': None,
            'intent_summary': None, 'column_map': None,
            'invitation_strength': None, 'invited_ids_reviewer': None, 'fidelity': None, 'independent_card_ref': None,
            'blind_provenance': None, 'drafted_by': DRAFTED_BY, 'status': STATUS,
            'notes': 'invited_ids_author labelled by hand after the intents were frozen (step A2); intent not rewritten for it.',
        }
        d = os.path.join(A, tid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'task.json'), 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=1, ensure_ascii=False)
            f.write('\n')
        head = ('# Reference solution for %s (stratum A). drafted_by: pkg:TASKS_RA; status: prepared'
                '.\n# Written 2026-11-11 to give the same canonical result on E0a, E0pa, E1, E2, E3 and E4.\n' % tid)
        with open(os.path.join(d, 'reference.py'), 'w', encoding='utf-8') as f:
            f.write(head + c['ref'])
    print('built %d A tasks' % len(INTENTS))


if __name__ == '__main__':
    build()
