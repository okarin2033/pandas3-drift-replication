"""Build candidate stratum-A tasks from the 40 separately written intents (REPAIR3, 2026-11-11; FULL_PREREG_AMENDMENT_8 items 3-5).

drafted_by: pkg:REPAIR3_INTEGRATE (integrator of the repair run); status: prepared (Amendment 9 item 1). Task texts are taken VERBATIM from tasks/A_intents_fresh/out/INTENTS_FRESH.tsv;
the build aborts unless that file matches its sha256 seal (INTENTS_FRESH.sha256) and the hash recorded below.
Cards (flags, variants, property checks) are set from the task text alone; property-check numbers are F-main fixture facts computed
here with the csv module; nothing here uses any run output. invited_ids_author were labelled by this integrator AFTER the intents were
written and sealed (the intent writer never saw the catalogue); intents are never rewritten for them.
Order flag rule used for this batch (conventions 137-139, section 3): order_significant = true when the text asks for rows ordered by a
key carried in the result (alphabetical, by value, in time order, top-N, or labels "in that order"; identity key __index__ where the
requested order is a listed or index order, Amendment 3); "in file order" alone is not flagged (rows carry their id), as in the 32
earlier A tasks and most M tasks.
Writes tasks/A_fresh/<id>/{task.json, reference.py}. These are CANDIDATES: Amendment 8 item 4 uses the first 40 - |R| of them in id
order once |R| is known; the rest are listed as unused. Usage: python3 -I -B tasks/A_fresh/tools/build_fresh_tasks.py
"""
import csv, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
S = os.path.abspath(os.path.join(PKG, '..', '..'))
INTENTS_TSV = os.path.join(S, 'tasks', 'A_intents_fresh', 'out', 'INTENTS_FRESH.tsv')
INTENTS_SEAL = os.path.join(S, 'tasks', 'A_intents_fresh', 'out', 'INTENTS_FRESH.sha256')
INTENTS_SHA = 'ffae987c06c8cf590f2a3ce39d9e90657440c403834b224300427065a65fe666'
DRAFTED_BY = 'pkg:REPAIR3_INTEGRATE'
STATUS = 'prepared'   # validator constant
NOTE = ('Intent written in a separate step that did not use the catalogue or the pre-registration (Amendment 8 item 3; '
        'INTENTS_FRESH.tsv sha256 ffae987c...e666). Card, reference and invited_ids_author drafted 2026-11-11 by pkg:REPAIR3_INTEGRATE '
        'after the intents were sealed; intent not rewritten. Prepared '
        '(Amendment 9).')


def load_intents():
    raw = open(INTENTS_TSV, 'rb').read()
    h = hashlib.sha256(raw).hexdigest()
    seal = open(INTENTS_SEAL, encoding='utf-8').read().split()[0]
    if h != INTENTS_SHA or seal != h:
        sys.exit('INTENTS_FRESH.tsv does not match its seal: %s' % h)
    out = {}
    with open(INTENTS_TSV, encoding='utf-8', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t', quoting=csv.QUOTE_NONE):
            out[r['id']] = (r['files'].split(','), r['task_text'])
    return out


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
RID, TRP, STA, WEA, FCH = rows('riders.csv'), rows('trips.csv'), rows('stations.csv'), rows('weather_hourly.csv'), rows('fare_changes.csv')
N_RIDERS, N_TRIPS, N_STATIONS, N_HOURS, N_FCH = len(RID), len(TRP), len(STA), len(WEA), len(FCH)
N_JOINED = sum(1 for r in RID if r['joined_on'])
N_BIRTH = sum(1 for r in RID if r['birth_year'])
N_TEMP_EMPTY = sum(1 for w in WEA if not w['temp_c'])
N_SEPT_TRIPS = sum(1 for t in TRP if t['started_at'][:7] == '2025-09')
PAYMENTS = sorted({t['payment'].strip().lower() for t in TRP})
MEMBERSHIPS = sorted({r['membership'].strip().lower() for r in RID})
HOME = sorted({r['home_district'].strip().lower() for r in RID})
DISTRICTS = sorted({s['district'].strip().lower() for s in STA})
SKIES = sorted({w['sky'].strip().lower() for w in WEA})
N_SURNAMES = len({r['display_name'].strip().split()[-1].lower() for r in RID})
N_BAL_RIDERS = sum(1 for r in RID if r['credit_balance'])

GEN_CHECKS = [{'check': 'no_null_text', 'args': {}}, {'check': 'no_all_missing_column', 'args': {}}]


def pc(check, **args):
    return {'check': check, 'args': args}


IDS = 'id columns (rider_id, station codes) may be written as integers without leading zeros'
CARDS = {}

CARDS['A_PIV_03'] = dict(
 invited=['R06'], order=True, keys=['__index__'],
 intended="Read trips.csv; clean payment (strip spaces, lower case); count trips per (payment, calendar month of started_at). "
 "Rows: payment methods in alphabetical order (index); columns 2025-09, 2025-10, 2025-11 in that order; whole-number counts, 0 for "
 "an empty combination.",
 notes='month column labels may be Periods or text; counts may be int or float; payment may be a column instead of the index',
 checks=[pc('n_groups_equals', n=len(PAYMENTS)), pc('no_nulls', columns=['2025-09', '2025-10', '2025-11']), pc('numeric_in_range', columns=['2025-09', '2025-10', '2025-11'], min=0, max=N_TRIPS),
         pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
months = ['2025-09', '2025-10', '2025-11']
counts = {}
for p, s in zip(trips['payment'].tolist(), trips['started_at'].tolist()):
    key = (p.strip().lower(), s[:7])
    counts[key] = counts.get(key, 0) + 1
pays = sorted({k[0] for k in counts})
result = pd.DataFrame([[counts.get((p, m), 0) for m in months] for p in pays], index=pd.Index(pays, name='payment'),
                      columns=months)
''')

CARDS['A_ENC_03'] = dict(
 invited=[], order=False, keys=[],
 intended="Read riders.csv keeping rider_id as text; clean membership (strip, lower case); one row per rider in file order with "
 "columns rider_id, is_annual, is_casual, is_monthly, each indicator 1 for the rider's level and 0 otherwise.",
 notes=IDS + '; indicators may be booleans; extra columns are not expected',
 checks=[pc('n_groups_equals', n=N_RIDERS), pc('columns_present', columns=['rider_id', 'is_annual', 'is_casual', 'is_monthly']),
         pc('no_nulls', columns=['rider_id', 'is_annual', 'is_casual', 'is_monthly']), pc('numeric_in_range', columns=['is_annual', 'is_casual', 'is_monthly'], min=0, max=1)],
 ref=r'''import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
levels = [m.strip().lower() for m in riders['membership'].tolist()]
result = pd.DataFrame({'rider_id': riders['rider_id'].tolist(),
                       'is_annual': [int(v == 'annual') for v in levels],
                       'is_casual': [int(v == 'casual') for v in levels],
                       'is_monthly': [int(v == 'monthly') for v in levels]})
''')

CARDS['A_UPD_03'] = dict(
 invited=['C01'], order=False, keys=[],
 intended="Read riders.csv; replace every negative credit_balance by 0 (empty balances stay empty); return the sum of the non-empty "
 "balances after the change, rounded to 2 decimals (one number).",
 notes='a numpy float is the same number',
 checks=[pc('result_kind', kind='scalar'), pc('numeric_in_range', columns=['__values__'], min=0, max=None)],
 ref=r'''import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
cents = [int(round(float(b) * 100)) for b in riders['credit_balance'].tolist() if b != '']
result = round(sum(max(c, 0) for c in cents) / 100, 2)
''')

CARDS['A_RPT_03'] = dict(
 invited=['G07'], order=True, keys=['hours', '__index__'],
 intended="Read weather_hourly.csv; clean sky (strip, lower case); per sky: hours = number of rows, mean_temp_c = mean of non-empty "
 "temp_c (1 decimal), total_rain_mm = sum of rain_mm (1 decimal), max_wind_kmh = largest wind_kmh. Index sky; rows sorted by hours "
 "descending, ties by sky ascending.",
 notes='sky may be a column instead of the index; max_wind_kmh may be float',
 checks=[pc('n_groups_equals', n=len(SKIES)), pc('counts_sum_to_rows', column='hours', expected=N_HOURS),
         pc('numeric_in_range', columns=['total_rain_mm'], min=0, max=None), pc('sorted_by', keys=['hours'], ascending=[False])],
 ref=r'''import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
g = {}
for sky, t, r, wd in zip(w['sky'].tolist(), w['temp_c'].tolist(), w['rain_mm'].tolist(), w['wind_kmh'].tolist()):
    d = g.setdefault(sky.strip().lower(), {'n': 0, 'ts': 0, 'tn': 0, 'rain': 0, 'wind': None})
    d['n'] += 1
    if t != '':
        d['ts'] += int(round(float(t) * 10))
        d['tn'] += 1
    d['rain'] += int(round(float(r) * 10))
    v = int(round(float(wd)))
    d['wind'] = v if d['wind'] is None else max(d['wind'], v)
order = sorted(g, key=lambda k: (-g[k]['n'], k))
result = pd.DataFrame({'hours': [g[k]['n'] for k in order],
                       'mean_temp_c': [round(g[k]['ts'] / (g[k]['tn'] * 10), 1) for k in order],
                       'total_rain_mm': [round(g[k]['rain'] / 10, 1) for k in order],
                       'max_wind_kmh': [g[k]['wind'] for k in order]}, index=pd.Index(order, name='sky'))
''')

CARDS['A_TXT_04'] = dict(
 invited=[], order=False, keys=[],
 intended="Read riders.csv; tidy display_name (strip surrounding spaces; every word with a capital first letter and the rest lower "
 "case; accented letters kept); return the number of distinct tidied names (one integer).",
 notes='a numpy integer is the same count',
 checks=[pc('result_kind', kind='scalar'), pc('numeric_in_range', columns=['__values__'], min=1, max=N_RIDERS)],
 ref=r'''import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
tidy = {' '.join(w[:1].upper() + w[1:].lower() for w in n.strip().split()) for n in riders['display_name'].tolist()}
result = len(tidy)
''')

CARDS['A_IMP_04'] = dict(
 invited=['C02'], order=False, keys=[],
 intended="Read riders.csv keeping rider_id as text; clean membership (strip, lower case); fill an empty birth_year with the median "
 "of the non-empty birth_year values of riders with the same cleaned membership, rounded down to a whole year; fill an empty "
 "credit_balance with 0. One row per rider in file order, columns rider_id, membership, birth_year, credit_balance.",
 notes=IDS + '; birth_year may be float',
 checks=[pc('n_groups_equals', n=N_RIDERS), pc('columns_present', columns=['rider_id', 'membership', 'birth_year', 'credit_balance']),
         pc('no_nulls', columns=['birth_year', 'credit_balance']), pc('numeric_in_range', columns=['birth_year'], min=1900, max=2025),
         pc('values_in_set', column='membership', values=MEMBERSHIPS)],
 ref=r'''import math
import statistics
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
memb = [m.strip().lower() for m in riders['membership'].tolist()]
years = riders['birth_year'].tolist()
by_level = {}
for m, y in zip(memb, years):
    if y != '':
        by_level.setdefault(m, []).append(int(y))
median = {m: int(math.floor(statistics.median(v))) for m, v in by_level.items()}
result = pd.DataFrame({'rider_id': riders['rider_id'].tolist(), 'membership': memb,
                       'birth_year': [int(y) if y != '' else median[m] for m, y in zip(memb, years)],
                       'credit_balance': [float(b) if b != '' else 0.0 for b in riders['credit_balance'].tolist()]})
''')

CARDS['A_CONV_04'] = dict(
 invited=['S03'], order=False, keys=[],
 intended="Read trips.csv; write duration_min as text H:MM (hours, colon, two-digit minutes; 75 -> 1:15, 9 -> 0:09), missing where "
 "duration_min is empty; a Series indexed by trip_id in file order.",
 notes='trip_id index may be text; the Series name is free',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_TRIPS)],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
out = []
for d in trips['duration_min'].tolist():
    if d == '':
        out.append(None)
    else:
        m = int(round(float(d)))
        out.append('%d:%02d' % (m // 60, m % 60))
result = pd.Series(out, index=pd.Index([int(x) for x in trips['trip_id'].tolist()], name='trip_id'), name='duration_hm')
''')

CARDS['A_BIN_04'] = dict(
 invited=['G01'], order=True, keys=['__index__'],
 intended="Read trips.csv; band distance_km into [0,2), [2,5), [5,10), [10, inf); per band: trips = number of trips, mean_fare = "
 "mean of non-empty fares (2 decimals). Index: the four band labels in that order.",
 notes='band labels may be spelled differently (e.g. interval notation); the band may be a column',
 checks=[pc('n_groups_equals', n=4), pc('counts_sum_to_rows', column='trips', expected=N_TRIPS),
         pc('numeric_in_range', columns=['mean_fare'], min=0, max=None), pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
labels = ['0-2', '2-5', '5-10', '10+']
n = [0, 0, 0, 0]
fs = [0, 0, 0, 0]
fn = [0, 0, 0, 0]
for d, f in zip(trips['distance_km'].tolist(), trips['fare'].tolist()):
    x = int(round(float(d) * 100))
    b = 0 if x < 200 else 1 if x < 500 else 2 if x < 1000 else 3
    n[b] += 1
    if f != '':
        fs[b] += int(round(float(f) * 100))
        fn[b] += 1
result = pd.DataFrame({'trips': n, 'mean_fare': [round(fs[i] / (fn[i] * 100), 2) for i in range(4)]},
                      index=pd.Index(labels, name='band'))
''')
# sorted_by on __index__ with text labels is not meaningful for band labels; replaced below by an order-free check list.
CARDS['A_BIN_04']['checks'] = CARDS['A_BIN_04']['checks'][:3]

CARDS['A_DATE_04'] = dict(
 invited=[], order=False, keys=[],
 intended="Read riders.csv keeping rider_id as text; for riders with a joined_on date: joined_weekday = English weekday name of "
 "joined_on, days_member = calendar days from joined_on to 2025-11-01. Columns rider_id, joined_weekday, days_member; riders without "
 "a date left out; file order.",
 notes=IDS,
 checks=[pc('n_groups_equals', n=N_JOINED), pc('numeric_in_range', columns=['days_member'], min=0, max=None),
         pc('values_in_set', column='joined_weekday', values=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']),
         pc('no_nulls', columns=['rider_id', 'joined_weekday', 'days_member'])],
 ref=r'''import datetime
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
end = datetime.date(2025, 11, 1)
ids, wd, days = [], [], []
for rid, j in zip(riders['rider_id'].tolist(), riders['joined_on'].tolist()):
    if j == '':
        continue
    d = datetime.date.fromisoformat(j)
    ids.append(rid)
    wd.append(names[d.weekday()])
    days.append((end - d).days)
result = pd.DataFrame({'rider_id': ids, 'joined_weekday': wd, 'days_member': days})
''')

CARDS['A_TS_04'] = dict(
 invited=['D03'], order=True, keys=['__index__'],
 intended="Read trips.csv; sum the non-empty fares per calendar month of started_at; a Series indexed by the month's last day as a "
 "date (2025-09-30, 2025-10-31, 2025-11-30) in time order, values rounded to 2 decimals.",
 notes='the index may be dates, timestamps at midnight, or YYYY-MM-DD text',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=3), pc('numeric_in_range', columns=['__values__'], min=0, max=None),
         pc('date_year_in_range', columns=['__index__'], min_year=2025, max_year=2025), pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import calendar
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
tot = {}
for s, f in zip(trips['started_at'].tolist(), trips['fare'].tolist()):
    if f != '':
        tot[s[:7]] = tot.get(s[:7], 0) + int(round(float(f) * 100))
keys = sorted(tot)
ends = ['%s-%02d' % (k, calendar.monthrange(int(k[:4]), int(k[5:7]))[1]) for k in keys]
result = pd.Series([round(tot[k] / 100, 2) for k in keys], index=pd.DatetimeIndex(pd.to_datetime(ends), name='month_end'),
                   name='fare_total')
''')

CARDS['A_TOP_04'] = dict(
 invited=['R03', 'G03'], order=True, keys=['payment', 'distance_km', 'trip_id'],
 intended="Read trips.csv; clean payment (strip, lower case); per payment the three trips with the largest distance_km (ties: smaller "
 "trip_id first); columns payment, trip_id, distance_km; 9 rows sorted by payment ascending, distance_km descending, trip_id ascending.",
 notes='trip_id may be text',
 checks=[pc('n_groups_equals', n=3 * len(PAYMENTS)), pc('values_in_set', column='payment', values=PAYMENTS),
         pc('sorted_by', keys=['payment', 'distance_km'], ascending=[True, False])],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
rows = sorted((p.strip().lower(), -int(round(float(d) * 100)), int(t), float(d))
              for t, p, d in zip(trips['trip_id'].tolist(), trips['payment'].tolist(), trips['distance_km'].tolist()))
seen, keep = {}, []
for r in rows:
    if seen.get(r[0], 0) < 3:
        keep.append(r)
        seen[r[0]] = seen.get(r[0], 0) + 1
result = pd.DataFrame({'payment': [r[0] for r in keep], 'trip_id': [r[2] for r in keep], 'distance_km': [r[3] for r in keep]})
''')

CARDS['A_MRG_04'] = dict(
 invited=['G07'], order=True, keys=['__index__'],
 intended="Read trips.csv and stations.csv (codes as text); attach the start station's district (strip spaces, each word capitalised, "
 "e.g. Old Town); per district: trips = number of trips, total_km = sum of distance_km (2 decimals). Index district, alphabetical.",
 notes='district labels may differ in letter case; district may be a column',
 checks=[pc('n_groups_equals', n=len(DISTRICTS)), pc('counts_sum_to_rows', column='trips', expected=N_TRIPS),
         pc('numeric_in_range', columns=['total_km'], min=0, max=None), pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
stations = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
district = {c: ' '.join(w[:1].upper() + w[1:].lower() for w in d.split())
            for c, d in zip(stations['station_code'].tolist(), stations['district'].tolist())}
n, km = {}, {}
for s, d in zip(trips['start_station'].tolist(), trips['distance_km'].tolist()):
    k = district[s]
    n[k] = n.get(k, 0) + 1
    km[k] = km.get(k, 0) + int(round(float(d) * 100))
keys = sorted(n)
result = pd.DataFrame({'trips': [n[k] for k in keys], 'total_km': [round(km[k] / 100, 2) for k in keys]},
                      index=pd.Index(keys, name='district'))
''')

CARDS['A_PIV_04'] = dict(
 invited=['R06'], order=True, keys=['__index__'],
 intended="Read riders.csv; clean home_district and membership (strip, lower case); rider counts with home districts as rows "
 "(alphabetical) and membership levels as columns (annual, casual, monthly), plus a last row and a last column named total holding "
 "the row totals, the column totals and the grand total (400).",
 notes='the margin row/column label may be spelled differently (e.g. All); counts may be float',
 checks=[pc('n_groups_equals', n=len(HOME) + 1), pc('no_nulls', columns=['annual', 'casual', 'monthly', 'total']), pc('numeric_in_range', columns=['annual', 'casual', 'monthly', 'total'], min=0, max=N_RIDERS)],
 ref=r'''import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
pairs = [(d.strip().lower(), m.strip().lower()) for d, m in zip(riders['home_district'].tolist(), riders['membership'].tolist())]
cols = ['annual', 'casual', 'monthly']
dists = sorted({d for d, _ in pairs})
cnt = {}
for p in pairs:
    cnt[p] = cnt.get(p, 0) + 1
data = [[cnt.get((d, m), 0) for m in cols] for d in dists]
data = [r + [sum(r)] for r in data]
data.append([sum(r[i] for r in data) for i in range(len(cols) + 1)])
result = pd.DataFrame(data, index=pd.Index(dists + ['total'], name='home_district'),
                      columns=pd.Index(cols + ['total'], name='membership'))
''')

CARDS['A_ENC_04'] = dict(
 invited=[], order=False, keys=[],
 intended="Read stations.csv keeping station_code as text; clean district (strip, lower case); code the six districts 0-5 in "
 "alphabetical order; a Series of these codes indexed by station_code in file order.",
 notes=IDS,
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_STATIONS), pc('no_nulls', columns=['__values__']),
         pc('numeric_in_range', columns=['__values__'], min=0, max=len(DISTRICTS) - 1)],
 ref=r'''import pandas as pd

stations = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
ds = [d.strip().lower() for d in stations['district'].tolist()]
code = {d: i for i, d in enumerate(sorted(set(ds)))}
result = pd.Series([code[d] for d in ds], index=pd.Index(stations['station_code'].tolist(), name='station_code'),
                   name='district_code')
''')

CARDS['A_UPD_04'] = dict(
 invited=['C01'], order=False, keys=[],
 intended="Read trips.csv; for trips whose started_at time of day is 07:00 to 09:59 multiply the fare by 1.1 and round that fare to "
 "2 decimals (other and empty fares unchanged); return the sum of the non-empty fares after the change, rounded to 2 decimals.",
 notes=('the reference rounds the floating-point product round(fare * 1.1, 2) per trip; about half of the fares end in 5 cents, so '
        'their exact product ends in half a cent and rounding half-even or half-up on the exact value may differ by 0.01 per such '
        'peak trip (intent writer flagged the per-trip rounding)'),
 checks=[pc('result_kind', kind='scalar'), pc('numeric_in_range', columns=['__values__'], min=0, max=None)],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
total = 0
for s, f in zip(trips['started_at'].tolist(), trips['fare'].tolist()):
    if f == '':
        continue
    v = float(f)
    if '07:00' <= s[11:16] <= '09:59':
        v = round(v * 1.1, 2)
    total += int(round(v * 100))
result = round(total / 100, 2)
''')

CARDS['A_RPT_04'] = dict(
 invited=['G07'], order=True, keys=['__index__'],
 intended="Read riders.csv; clean home_district (strip, lower case); per district: riders = count, median_birth_year = median of "
 "non-empty birth_year (1 decimal), mean_balance = mean of non-empty credit_balance (2 decimals), negative_balances = number of "
 "riders with credit_balance < 0. Index home_district, alphabetical.",
 notes='home_district may be a column',
 checks=[pc('n_groups_equals', n=len(HOME)), pc('counts_sum_to_rows', column='riders', expected=N_RIDERS),
         pc('numeric_in_range', columns=['median_birth_year'], min=1900, max=2025), pc('numeric_in_range', columns=['negative_balances'], min=0, max=N_RIDERS),
         pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import statistics
import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
g = {}
for d, y, b in zip(riders['home_district'].tolist(), riders['birth_year'].tolist(), riders['credit_balance'].tolist()):
    e = g.setdefault(d.strip().lower(), {'n': 0, 'years': [], 'bal': []})
    e['n'] += 1
    if y != '':
        e['years'].append(int(y))
    if b != '':
        e['bal'].append(int(round(float(b) * 100)))
keys = sorted(g)
result = pd.DataFrame({'riders': [g[k]['n'] for k in keys],
                       'median_birth_year': [round(float(statistics.median(g[k]['years'])), 1) for k in keys],
                       'mean_balance': [round(sum(g[k]['bal']) / (len(g[k]['bal']) * 100), 2) for k in keys],
                       'negative_balances': [sum(1 for c in g[k]['bal'] if c < 0) for k in keys]},
                      index=pd.Index(keys, name='home_district'))
''')

CARDS['A_TXT_05'] = dict(
 invited=['S05'], order=False, keys=[],
 intended="Read stations.csv keeping station_code as text; slug of station_name: lower case, accented letters replaced by their base "
 "letter (é->e, ü->u, å->a), spaces replaced by hyphens; a Series of slugs indexed by station_code in file order.",
 notes=IDS,
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_STATIONS), pc('no_nulls', columns=['__values__'])],
 ref=r'''import unicodedata
import pandas as pd

stations = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)


def slug(name):
    base = ''.join(ch for ch in unicodedata.normalize('NFKD', name.lower()) if not unicodedata.combining(ch))
    return base.replace(' ', '-')


result = pd.Series([slug(n) for n in stations['station_name'].tolist()],
                   index=pd.Index(stations['station_code'].tolist(), name='station_code'), name='slug')
''')

CARDS['A_IMP_05'] = dict(
 invited=['C02'], order=True, keys=['__index__'],
 intended="Read weather_hourly.csv; for each empty temp_c, linear interpolation in time between the nearest non-empty hours before "
 "and after; a Series holding only the filled values, rounded to 2 decimals, indexed by observed_at as written, in time order.",
 notes='the index may be timestamps instead of text',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_TEMP_EMPTY), pc('no_nulls', columns=['__values__']),
         pc('numeric_in_range', columns=['__values__'], min=-40, max=50), pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import datetime
import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
obs = w['observed_at'].tolist()
when = [datetime.datetime.strptime(o, '%Y-%m-%d %H:%M') for o in obs]
temp = [float(t) if t != '' else None for t in w['temp_c'].tolist()]
labels, values = [], []
for i, t in enumerate(temp):
    if t is not None:
        continue
    j = i - 1
    while temp[j] is None:
        j -= 1
    k = i + 1
    while temp[k] is None:
        k += 1
    frac = (when[i] - when[j]).total_seconds() / (when[k] - when[j]).total_seconds()
    labels.append(obs[i])
    values.append(round(temp[j] + (temp[k] - temp[j]) * frac, 2))
result = pd.Series(values, index=pd.Index(labels, name='observed_at'), name='temp_c')
''')

CARDS['A_CONV_05'] = dict(
 invited=['S03'], order=False, keys=[],
 intended="Read riders.csv keeping rider_id as text; write credit_balance as text with an explicit sign and two decimals (12.5 -> "
 "+12.50, -3.2 -> -3.20, 0 -> +0.00) and n/a for an empty balance; a Series indexed by rider_id in file order.",
 notes=IDS,
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_RIDERS), pc('no_nulls', columns=['__values__'])],
 ref=r'''import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
out = []
for b in riders['credit_balance'].tolist():
    if b == '':
        out.append('n/a')
        continue
    c = int(round(float(b) * 100))
    out.append('%s%d.%02d' % ('-' if c < 0 else '+', abs(c) // 100, abs(c) % 100))
result = pd.Series(out, index=pd.Index(riders['rider_id'].tolist(), name='rider_id'), name='balance_text')
''')

CARDS['A_BIN_05'] = dict(
 invited=['G01'], order=True, keys=['__index__'],
 intended="Read riders.csv; riders with a birth_year only; age = 2025 - birth_year; bands under 25, 25-39, 40-59, 60+; per band: "
 "riders = count, mean_balance = mean of non-empty credit_balance (2 decimals). Index: the four band labels in that order.",
 notes='band labels may be spelled differently (e.g. interval notation); the band may be a column',
 checks=[pc('n_groups_equals', n=4), pc('counts_sum_to_rows', column='riders', expected=N_BIRTH)],
 ref=r'''import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
labels = ['under 25', '25-39', '40-59', '60+']
n = [0, 0, 0, 0]
bs = [0, 0, 0, 0]
bn = [0, 0, 0, 0]
for y, b in zip(riders['birth_year'].tolist(), riders['credit_balance'].tolist()):
    if y == '':
        continue
    age = 2025 - int(y)
    k = 0 if age < 25 else 1 if age < 40 else 2 if age < 60 else 3
    n[k] += 1
    if b != '':
        bs[k] += int(round(float(b) * 100))
        bn[k] += 1
result = pd.DataFrame({'riders': n, 'mean_balance': [round(bs[i] / (bn[i] * 100), 2) for i in range(4)]},
                      index=pd.Index(labels, name='age_band'))
''')

CARDS['A_DATE_05'] = dict(
 invited=['D01'], order=False, keys=[],
 intended="Read trips.csv; read started_at as a UTC time; start_epoch = whole seconds since 1970-01-01 00:00 UTC; "
 "start_day_of_month = day of the month (1-31). Columns trip_id, start_epoch, start_day_of_month; one row per trip, file order.",
 notes='trip_id may be text',
 checks=[pc('n_groups_equals', n=N_TRIPS), pc('no_nulls', columns=['trip_id', 'start_epoch', 'start_day_of_month']),
         pc('numeric_in_range', columns=['start_epoch'], min=1756684800, max=1762041600),
         pc('numeric_in_range', columns=['start_day_of_month'], min=1, max=31)],
 ref=r'''import calendar
import datetime
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
when = [datetime.datetime.strptime(s, '%Y-%m-%d %H:%M') for s in trips['started_at'].tolist()]
result = pd.DataFrame({'trip_id': [int(t) for t in trips['trip_id'].tolist()],
                       'start_epoch': [calendar.timegm(d.timetuple()) for d in when],
                       'start_day_of_month': [d.day for d in when]})
''')

CARDS['A_TS_05'] = dict(
 invited=[], order=True, keys=['__index__'],
 intended="Read weather_hourly.csv; daily mean of non-empty temp_c for each day of September 2025; then the mean over a 3-day window "
 "ending on each day (the day and the two before), missing for 1 and 2 September; a Series indexed by date in time order, rounded "
 "to 2 decimals.",
 notes='the index may be dates, timestamps at midnight, or YYYY-MM-DD text',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=30), pc('numeric_in_range', columns=['__values__'], min=-40, max=50),
         pc('date_year_in_range', columns=['__index__'], min_year=2025, max_year=2025), pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
tot, cnt = {}, {}
for o, t in zip(w['observed_at'].tolist(), w['temp_c'].tolist()):
    d = o[:10]
    if d[:7] != '2025-09':
        continue
    tot.setdefault(d, 0)
    cnt.setdefault(d, 0)
    if t != '':
        tot[d] += int(round(float(t) * 10))
        cnt[d] += 1
days = sorted(tot)
daily = [tot[d] / (cnt[d] * 10) for d in days]
roll = [None if i < 2 else round((daily[i - 2] + daily[i - 1] + daily[i]) / 3, 2) for i in range(len(days))]
result = pd.Series(roll, index=pd.DatetimeIndex(pd.to_datetime(days), name='date'), name='temp_c_3day', dtype='float64')
''')

CARDS['A_TOP_05'] = dict(
 invited=['R03', 'G03'], order=True, keys=['district', 'docks', 'station_code'],
 intended="Read stations.csv keeping station_code as text; clean district (strip, lower case); per district the two stations with "
 "the most docks (ties: earlier opened_on, then smaller station_code); columns district, station_code, station_name, docks; 12 rows "
 "sorted by district ascending, docks descending, opened_on ascending, station_code ascending.",
 notes=IDS,
 checks=[pc('n_groups_equals', n=2 * len(DISTRICTS)), pc('values_in_set', column='district', values=DISTRICTS),
         pc('sorted_by', keys=['district', 'docks'], ascending=[True, False])],
 ref=r'''import pandas as pd

st = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
rows = sorted((d.strip().lower(), -int(k), o, c, n, int(k)) for c, n, d, k, o in
              zip(st['station_code'].tolist(), st['station_name'].tolist(), st['district'].tolist(), st['docks'].tolist(),
                  st['opened_on'].tolist()))
seen, keep = {}, []
for r in rows:
    if seen.get(r[0], 0) < 2:
        keep.append(r)
        seen[r[0]] = seen.get(r[0], 0) + 1
result = pd.DataFrame({'district': [r[0] for r in keep], 'station_code': [r[3] for r in keep],
                       'station_name': [r[4] for r in keep], 'docks': [r[5] for r in keep]})
''')

CARDS['A_MRG_05'] = dict(
 invited=['G07'], order=True, keys=['__index__'],
 intended="Read trips.csv and riders.csv; attach each trip's rider membership (strip, lower case); per membership: trips = count, "
 "riders = number of distinct riders with trips, mean_fare = mean of non-empty fares (2 decimals). Index membership, alphabetical.",
 notes='membership may be a column',
 checks=[pc('n_groups_equals', n=len(MEMBERSHIPS)), pc('counts_sum_to_rows', column='trips', expected=N_TRIPS),
         pc('numeric_in_range', columns=['mean_fare'], min=0, max=None), pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
memb = {r: m.strip().lower() for r, m in zip(riders['rider_id'].tolist(), riders['membership'].tolist())}
n, who, fs, fn = {}, {}, {}, {}
for r, f in zip(trips['rider_id'].tolist(), trips['fare'].tolist()):
    k = memb[r]
    n[k] = n.get(k, 0) + 1
    who.setdefault(k, set()).add(r)
    if f != '':
        fs[k] = fs.get(k, 0) + int(round(float(f) * 100))
        fn[k] = fn.get(k, 0) + 1
keys = sorted(n)
result = pd.DataFrame({'trips': [n[k] for k in keys], 'riders': [len(who[k]) for k in keys],
                       'mean_fare': [round(fs[k] / (fn[k] * 100), 2) for k in keys]}, index=pd.Index(keys, name='membership'))
''')

CARDS['A_PIV_05'] = dict(
 invited=['R04'], order=True, keys=['observed_at', 'measure'],
 intended="Read weather_hourly.csv; long form with one row per (hour, measure) for temp_c, rain_mm, wind_kmh; columns observed_at, "
 "measure (the column name), value; rows with an empty temp_c dropped; sorted by observed_at, then measure alphabetically; default "
 "index 0..n-1.",
 notes='observed_at may be timestamps instead of text; value may be float throughout',
 checks=[pc('n_groups_equals', n=3 * N_HOURS - N_TEMP_EMPTY), pc('no_nulls', columns=['value']),
         pc('values_in_set', column='measure', values=['rain_mm', 'temp_c', 'wind_kmh']),
         pc('columns_present', columns=['observed_at', 'measure', 'value']), pc('sorted_by', keys=['observed_at', 'measure'], ascending=[True, True])],
 ref=r'''import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
rows = []
for o, t, r, wd in zip(w['observed_at'].tolist(), w['temp_c'].tolist(), w['rain_mm'].tolist(), w['wind_kmh'].tolist()):
    for name, val in (('rain_mm', r), ('temp_c', t), ('wind_kmh', wd)):
        if val != '':
            rows.append((o, name, float(val)))
rows.sort(key=lambda x: (x[0], x[1]))
result = pd.DataFrame({'observed_at': [x[0] for x in rows], 'measure': [x[1] for x in rows], 'value': [x[2] for x in rows]})
''')

CARDS['A_ENC_05'] = dict(
 invited=[], order=False, keys=[],
 intended="Read trips.csv; clean payment (strip, lower case); replace it by the share of all 1500 trips with that payment (4 "
 "decimals); a Series indexed by trip_id in file order.",
 notes='trip_id index may be text',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_TRIPS), pc('no_nulls', columns=['__values__']), pc('rate_in_unit_interval', columns=['__values__'])],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
pays = [p.strip().lower() for p in trips['payment'].tolist()]
cnt = {}
for p in pays:
    cnt[p] = cnt.get(p, 0) + 1
share = {p: round(c / len(pays), 4) for p, c in cnt.items()}
result = pd.Series([share[p] for p in pays], index=pd.Index([int(t) for t in trips['trip_id'].tolist()], name='trip_id'),
                   name='payment_share')
''')

CARDS['A_UPD_05'] = dict(
 invited=['C01'], order=True, keys=['__index__'],
 intended="Read riders.csv; clean membership (strip, lower case); riders with level monthly and a joined_on before 2023-01-01 become "
 "annual (empty joined_on unchanged); a Series counting riders per level, indexed by level in alphabetical order.",
 notes='counts may be a one-column table',
 checks=[pc('n_groups_equals', n=len(MEMBERSHIPS)), pc('counts_sum_to_rows', column='__values__', expected=N_RIDERS),
         pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
cnt = {}
for m, j in zip(riders['membership'].tolist(), riders['joined_on'].tolist()):
    m = m.strip().lower()
    if m == 'monthly' and j != '' and j < '2023-01-01':
        m = 'annual'
    cnt[m] = cnt.get(m, 0) + 1
keys = sorted(cnt)
result = pd.Series([cnt[k] for k in keys], index=pd.Index(keys, name='membership'), name='riders')
''')

CARDS['A_RPT_05'] = dict(
 invited=[], order=True, keys=['__index__'],
 intended="Read trips.csv; a Series with labels in this order: trips (rows), riders (distinct rider_id), total_km (sum of distance_km, "
 "2 decimals), mean_duration_min (mean of non-empty duration_min, 1 decimal), mean_rating (mean of non-empty rating, 2 decimals), "
 "missing_fare (number of empty fares).",
 notes='values may be float throughout',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=6), pc('no_nulls', columns=['__values__']), pc('numeric_in_range', columns=['__values__'], min=0, max=None)],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
dist = sum(int(round(float(d) * 100)) for d in trips['distance_km'].tolist())
dur = [int(round(float(d))) for d in trips['duration_min'].tolist() if d != '']
rat = [int(round(float(r))) for r in trips['rating'].tolist() if r != '']
values = [len(trips), len(set(trips['rider_id'].tolist())), round(dist / 100, 2), round(sum(dur) / len(dur), 1),
          round(sum(rat) / len(rat), 2), sum(1 for f in trips['fare'].tolist() if f == '')]
result = pd.Series([float(v) for v in values],
                   index=['trips', 'riders', 'total_km', 'mean_duration_min', 'mean_rating', 'missing_fare'], name='overview')
''')
# the Series labels are listed, not sorted: a sorted_by check does not apply (validator note accepted).

CARDS['A_TXT_06'] = dict(
 invited=[], order=True, keys=['__values__', '__index__'],
 intended="Read riders.csv; surname = last word of display_name (stripped; capital first letter, rest lower case); a Series counting "
 "riders per surname, sorted by count descending, ties by surname ascending.",
 notes='surname may be a column of a one-column table',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_SURNAMES), pc('counts_sum_to_rows', column='__values__', expected=N_RIDERS),
         pc('sorted_by', keys=['__values__'], ascending=[False])],
 ref=r'''import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
cnt = {}
for n in riders['display_name'].tolist():
    w = n.strip().split()[-1]
    s = w[:1].upper() + w[1:].lower()
    cnt[s] = cnt.get(s, 0) + 1
keys = sorted(cnt, key=lambda k: (-cnt[k], k))
result = pd.Series([cnt[k] for k in keys], index=pd.Index(keys, name='surname'), name='riders')
''')

CARDS['A_IMP_06'] = dict(
 invited=['C02'], order=False, keys=[],
 intended="Read trips.csv; fill an empty duration_min with the mean of the non-empty durations rounded to a whole minute; fill an "
 "empty rating with the most common rating (smallest on a tie); columns trip_id, duration_min, rating; one row per trip, file order.",
 notes='duration_min and rating may be float; trip_id may be text',
 checks=[pc('n_groups_equals', n=N_TRIPS), pc('no_nulls', columns=['duration_min', 'rating']), pc('numeric_in_range', columns=['rating'], min=1, max=5),
         pc('numeric_in_range', columns=['duration_min'], min=0, max=None)],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
dur = [int(round(float(d))) for d in trips['duration_min'].tolist() if d != '']
fill_d = int(round(sum(dur) / len(dur)))
cnt = {}
for r in trips['rating'].tolist():
    if r != '':
        v = int(round(float(r)))
        cnt[v] = cnt.get(v, 0) + 1
top = max(cnt.values())
fill_r = min(k for k, v in cnt.items() if v == top)
result = pd.DataFrame({'trip_id': [int(t) for t in trips['trip_id'].tolist()],
                       'duration_min': [int(round(float(d))) if d != '' else fill_d for d in trips['duration_min'].tolist()],
                       'rating': [int(round(float(r))) if r != '' else fill_r for r in trips['rating'].tolist()]})
''')

CARDS['A_CONV_06'] = dict(
 invited=[], order=False, keys=[],
 intended="Read fare_changes.csv keeping station_code as text; new_base_fare in whole cents (1.50 -> 150), missing where empty; a "
 "Series indexed by station_code in file order.",
 notes=IDS + '; cents may be float or a nullable integer',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_FCH), pc('numeric_in_range', columns=['__values__'], min=0, max=None)],
 ref=r'''import pandas as pd

fc = pd.read_csv('fare_changes.csv', dtype=str, keep_default_na=False)
cents = [int(round(float(v) * 100)) if v != '' else None for v in fc['new_base_fare'].tolist()]
result = pd.Series(cents, index=pd.Index(fc['station_code'].tolist(), name='station_code'), name='new_base_fare_cents',
                   dtype='float64')
''')

CARDS['A_BIN_06'] = dict(
 invited=['G01'], order=True, keys=['__index__'],
 intended="Read weather_hourly.csv; band wind_kmh into calm (0-5), light (6-19), moderate (20-38), strong (39 and above); per band: "
 "hours = count, total_rain_mm = sum of rain_mm (1 decimal), mean_temp_c = mean of non-empty temp_c (1 decimal). Index: the four "
 "band labels in that order.",
 notes='the band may be a column',
 checks=[pc('n_groups_equals', n=4), pc('counts_sum_to_rows', column='hours', expected=N_HOURS),
         pc('numeric_in_range', columns=['total_rain_mm'], min=0, max=None)],
 ref=r'''import pandas as pd

w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
labels = ['calm', 'light', 'moderate', 'strong']
n = [0, 0, 0, 0]
rain = [0, 0, 0, 0]
ts = [0, 0, 0, 0]
tn = [0, 0, 0, 0]
for wd, r, t in zip(w['wind_kmh'].tolist(), w['rain_mm'].tolist(), w['temp_c'].tolist()):
    v = float(wd)
    k = 0 if v <= 5 else 1 if v <= 19 else 2 if v <= 38 else 3
    n[k] += 1
    rain[k] += int(round(float(r) * 10))
    if t != '':
        ts[k] += int(round(float(t) * 10))
        tn[k] += 1
result = pd.DataFrame({'hours': n, 'total_rain_mm': [round(x / 10, 1) for x in rain],
                       'mean_temp_c': [round(ts[i] / (tn[i] * 10), 1) for i in range(4)]}, index=pd.Index(labels, name='wind_band'))
''')

CARDS['A_DATE_06'] = dict(
 invited=[], order=False, keys=[],
 intended="Read stations.csv keeping station_code as text; opened_on as a date; open_year, open_day_of_year (1-366) and years_open = "
 "completed years from opened_on to 2025-11-01. Columns station_code, open_year, open_day_of_year, years_open; file order.",
 notes=IDS,
 checks=[pc('n_groups_equals', n=N_STATIONS), pc('no_nulls', columns=['open_year', 'open_day_of_year', 'years_open']), pc('numeric_in_range', columns=['open_day_of_year'], min=1, max=366),
         pc('numeric_in_range', columns=['years_open'], min=0, max=None), pc('numeric_in_range', columns=['open_year'], min=1900, max=2025)],
 ref=r'''import datetime
import pandas as pd

st = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
ref = datetime.date(2025, 11, 1)
days = [datetime.date.fromisoformat(o) for o in st['opened_on'].tolist()]
result = pd.DataFrame({'station_code': st['station_code'].tolist(), 'open_year': [d.year for d in days],
                       'open_day_of_year': [d.timetuple().tm_yday for d in days],
                       'years_open': [ref.year - d.year - ((ref.month, ref.day) < (d.month, d.day)) for d in days]})
''')

CARDS['A_TS_06'] = dict(
 invited=['D04'], order=True, keys=['__index__'],
 intended="Read trips.csv; trips per calendar day of started_at for every day from 2025-09-01 to 2025-11-01 (0 for days without "
 "trips); then the mean over a 7-day window ending on each day (the day and the six before), missing for the first six days; a "
 "Series indexed by date in time order, rounded to 2 decimals.",
 notes='the index may be dates, timestamps at midnight, or YYYY-MM-DD text',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=62), pc('numeric_in_range', columns=['__values__'], min=0, max=None),
         pc('date_year_in_range', columns=['__index__'], min_year=2025, max_year=2025), pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import datetime
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
cnt = {}
for s in trips['started_at'].tolist():
    cnt[s[:10]] = cnt.get(s[:10], 0) + 1
start, end = datetime.date(2025, 9, 1), datetime.date(2025, 11, 1)
days = [(start + datetime.timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]
c = [cnt.get(d, 0) for d in days]
roll = [None if i < 6 else round(sum(c[i - 6:i + 1]) / 7, 2) for i in range(len(days))]
result = pd.Series(roll, index=pd.DatetimeIndex(pd.to_datetime(days), name='date'), name='trips_7day', dtype='float64')
''')

CARDS['A_TOP_06'] = dict(
 invited=['R03', 'G03'], order=True, keys=['membership', 'credit_balance', 'rider_id'],
 intended="Read riders.csv keeping rider_id as text; clean membership (strip, lower case); riders with a non-empty credit_balance; per "
 "membership the five highest balances (ties: smaller rider_id first); columns membership, rider_id, credit_balance; 15 rows sorted "
 "by membership ascending, credit_balance descending, rider_id ascending.",
 notes=IDS,
 checks=[pc('n_groups_equals', n=5 * len(MEMBERSHIPS)), pc('values_in_set', column='membership', values=MEMBERSHIPS),
         pc('sorted_by', keys=['membership', 'credit_balance'], ascending=[True, False])],
 ref=r'''import pandas as pd

riders = pd.read_csv('riders.csv', dtype=str, keep_default_na=False)
rows = sorted((m.strip().lower(), -int(round(float(b) * 100)), r, float(b))
              for r, m, b in zip(riders['rider_id'].tolist(), riders['membership'].tolist(), riders['credit_balance'].tolist())
              if b != '')
seen, keep = {}, []
for x in rows:
    if seen.get(x[0], 0) < 5:
        keep.append(x)
        seen[x[0]] = seen.get(x[0], 0) + 1
result = pd.DataFrame({'membership': [x[0] for x in keep], 'rider_id': [x[2] for x in keep], 'credit_balance': [x[3] for x in keep]})
''')

CARDS['A_MRG_06'] = dict(
 invited=['G07'], order=True, keys=['__index__'],
 intended="Read trips.csv and weather_hourly.csv; trips that started in September 2025; match each to the weather row whose "
 "observed_at equals started_at cut down to the whole hour; clean sky (strip, lower case); per sky: trips = count, mean_duration_min "
 "= mean of non-empty duration_min (1 decimal). Index sky, alphabetical.",
 notes='sky may be a column',
 checks=[pc('n_groups_equals', n=len(SKIES)), pc('counts_sum_to_rows', column='trips', expected=N_SEPT_TRIPS),
         pc('numeric_in_range', columns=['mean_duration_min'], min=0, max=None), pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
w = pd.read_csv('weather_hourly.csv', dtype=str, keep_default_na=False)
sky = {o: s.strip().lower() for o, s in zip(w['observed_at'].tolist(), w['sky'].tolist())}
n, ds, dn = {}, {}, {}
for s, d in zip(trips['started_at'].tolist(), trips['duration_min'].tolist()):
    if s[:7] != '2025-09':
        continue
    k = sky[s[:13] + ':00']
    n[k] = n.get(k, 0) + 1
    if d != '':
        ds[k] = ds.get(k, 0) + int(round(float(d)))
        dn[k] = dn.get(k, 0) + 1
keys = sorted(n)
result = pd.DataFrame({'trips': [n[k] for k in keys], 'mean_duration_min': [round(ds[k] / dn[k], 1) for k in keys]},
                      index=pd.Index(keys, name='sky'))
''')

CARDS['A_PIV_06'] = dict(
 invited=['R06'], order=True, keys=['__index__'],
 intended="Read trips.csv; clean payment (strip, lower case); mean distance_km per (weekday of started_at, payment); rows Monday to "
 "Sunday in that order, columns payment methods in alphabetical order; values rounded to 2 decimals.",
 notes='weekday labels may be spelled differently in letter case',
 checks=[pc('n_groups_equals', n=7), pc('no_nulls', columns=PAYMENTS), pc('numeric_in_range', columns=PAYMENTS, min=0, max=None)],
 ref=r'''import datetime
import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
s, n = {}, {}
for st, p, d in zip(trips['started_at'].tolist(), trips['payment'].tolist(), trips['distance_km'].tolist()):
    k = (datetime.date.fromisoformat(st[:10]).weekday(), p.strip().lower())
    s[k] = s.get(k, 0) + int(round(float(d) * 100))
    n[k] = n.get(k, 0) + 1
pays = sorted({k[1] for k in n})
data = [[round(s[(i, p)] / (n[(i, p)] * 100), 2) if (i, p) in n else None for p in pays] for i in range(7)]
result = pd.DataFrame(data, index=pd.Index(names, name='weekday'), columns=pd.Index(pays, name='payment'))
''')

CARDS['A_ENC_06'] = dict(
 invited=['G07'], order=False, keys=[],
 intended="Read trips.csv; per start_station the mean of the non-empty ratings of all trips that started there (2 decimals); a Series "
 "giving each trip its start station's value, indexed by trip_id, one per trip in file order.",
 notes='trip_id index may be text',
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_TRIPS), pc('numeric_in_range', columns=['__values__'], min=1, max=5)],
 ref=r'''import pandas as pd

trips = pd.read_csv('trips.csv', dtype=str, keep_default_na=False)
s, n = {}, {}
for st, r in zip(trips['start_station'].tolist(), trips['rating'].tolist()):
    if r != '':
        s[st] = s.get(st, 0) + int(round(float(r)))
        n[st] = n.get(st, 0) + 1
enc = {k: round(s[k] / n[k], 2) for k in n}
result = pd.Series([enc.get(st) for st in trips['start_station'].tolist()],
                   index=pd.Index([int(t) for t in trips['trip_id'].tolist()], name='trip_id'), name='station_rating', dtype='float64')
''')

CARDS['A_UPD_06'] = dict(
 invited=['C01'], order=False, keys=[],
 intended="Read stations.csv and fare_changes.csv keeping station codes as text; base_fare = 1.00 for every station; for stations in "
 "fare_changes.csv with effective_from on or before 2025-11-30 and a non-empty new_base_fare, base_fare = new_base_fare; a Series "
 "indexed by station_code in the order of stations.csv.",
 notes=IDS,
 checks=[pc('result_kind', kind='series'), pc('n_groups_equals', n=N_STATIONS), pc('no_nulls', columns=['__values__']), pc('numeric_in_range', columns=['__values__'], min=0, max=None)],
 ref=r'''import pandas as pd

st = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
fc = pd.read_csv('fare_changes.csv', dtype=str, keep_default_na=False)
fare = {c: 1.0 for c in st['station_code'].tolist()}
for c, e, v in zip(fc['station_code'].tolist(), fc['effective_from'].tolist(), fc['new_base_fare'].tolist()):
    if e <= '2025-11-30' and v != '' and c in fare:
        fare[c] = float(v)
result = pd.Series([fare[c] for c in st['station_code'].tolist()], index=pd.Index(st['station_code'].tolist(), name='station_code'),
                   name='base_fare')
''')

CARDS['A_RPT_06'] = dict(
 invited=[], order=True, keys=['__index__'],
 intended="Read stations.csv; clean district (strip spaces, each word capitalised, e.g. Old Town); per district: stations = count, "
 "total_docks = sum of docks, mean_docks (1 decimal), first_opened and last_opened = earliest and latest opened_on as YYYY-MM-DD "
 "text. Index district, alphabetical.",
 notes='district labels may differ in letter case; district may be a column',
 checks=[pc('n_groups_equals', n=len(DISTRICTS)), pc('counts_sum_to_rows', column='stations', expected=N_STATIONS),
         pc('date_year_in_range', columns=['first_opened', 'last_opened'], min_year=2000, max_year=2025),
         pc('sorted_by', keys=['__index__'], ascending=[True])],
 ref=r'''import pandas as pd

st = pd.read_csv('stations.csv', dtype=str, keep_default_na=False)
g = {}
for d, k, o in zip(st['district'].tolist(), st['docks'].tolist(), st['opened_on'].tolist()):
    key = ' '.join(w[:1].upper() + w[1:].lower() for w in d.split())
    e = g.setdefault(key, {'docks': [], 'opened': []})
    e['docks'].append(int(k))
    e['opened'].append(o)
keys = sorted(g)
result = pd.DataFrame({'stations': [len(g[k]['docks']) for k in keys], 'total_docks': [sum(g[k]['docks']) for k in keys],
                       'mean_docks': [round(sum(g[k]['docks']) / len(g[k]['docks']), 1) for k in keys],
                       'first_opened': [min(g[k]['opened']) for k in keys], 'last_opened': [max(g[k]['opened']) for k in keys]},
                      index=pd.Index(keys, name='district'))
''')


def build():
    intents = load_intents()
    desc = descriptions()
    assert list(CARDS) == list(intents), 'cards and intents differ (order included)'
    for tid, (files, text) in intents.items():
        c = CARDS[tid]
        assert bool(c['keys']) == c['order'], tid
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
            'blind_provenance': None, 'drafted_by': DRAFTED_BY, 'status': STATUS, 'notes': NOTE,
        }
        d = os.path.join(PKG, tid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'task.json'), 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=1, ensure_ascii=False)
            f.write('\n')
        head = ('# Reference solution for %s (stratum A, fresh intent). drafted_by: pkg:REPAIR3_INTEGRATE; status: prepared'
                ' (Amendment 9).\n# Written 2026-11-11 to give the same canonical result on E0a, E0pa, '
                'E1, E2, E3 and E4.\n' % tid)
        with open(os.path.join(d, 'reference.py'), 'w', encoding='utf-8') as f:
            f.write(head + c['ref'])
    print('built %d candidate A tasks in %s' % (len(intents), os.path.relpath(PKG, S)))


if __name__ == '__main__':
    build()
