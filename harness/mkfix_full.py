# Fixture generator for the full study (FULL_PREREG.md section 4.4; STAGE2_TASKS.md T3). Standard library only.
# Written 2026-11-11 by pkg:FIX. drafted_by: pkg:FIX; status: prepared.
#
# usage: python3 -I -B harness/mkfix_full.py [--out DIR]        (default DIR = <study>/fixtures)
#
# Writes, for every file below, three variants with the same columns and row counts:
#   <DIR>/main/<FAMILY|GEN>/<name>.csv    F-main  (primary; moderately messy, family-specific)
#   <DIR>/clean/<FAMILY|GEN>/<name>.csv   F-clean (no missing values, no letter-case or space noise)
#   <DIR>/dirty/<FAMILY|GEN>/<name>.csv   F-dirty (F-main plus: about 5% of numeric cells '$'-prefixed or 'N/A',
#                                                   every numeric column with at least one '$' cell so that it reads as
#                                                   text, and a whitespace-only label in every category-like column)
#   <DIR>/descriptions.tsv   one fixture-true line per file, describing F-main (numbers measured from the F-main rows)
#   <DIR>/columns.tsv        path, column, kind (generator column kinds; for task authors and checks)
#   <DIR>/row_files.tsv      confirmed catalogue row -> F-main file(s) and the column roles it uses
# Everything is a function of SEED = 20261111 and the file path; nothing reads the clock or the environment, so two
# runs give byte-identical files. No pilot fixture, column set or content is used (checked by logs/fix/tools/check_fixtures.py).
import argparse, csv, datetime as dt, hashlib, io, os, random, sys

SEED = 20261111
HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
VARIANTS = ('main', 'clean', 'dirty')
NUMERIC_KINDS = ('int', 'float', 'epoch')          # corrupted in F-dirty; 'id' and 'zpad' columns are identifiers
CAT_KINDS = ('cat',)

FIRST = ['Ana', 'José', 'Zoë', 'Łukasz', 'Søren', 'Chloé', 'Mateo', 'Ingrid', 'Björn', 'Aiko', 'Noah', 'Priya', 'Émile',
         'Farah', 'Kenji', 'Olga', 'Raúl', 'Sanna', 'Tomás', 'Yusuf', 'Mia', 'Dmitri', 'Leila', 'Nils', 'Ines', 'Hugo']
LAST = ['Müller', 'Okafor', 'Nakamura', 'García', 'Kowalski', 'Dubois', 'Silva', 'Jensen', 'Ivanova', 'Haddad', 'Novak',
        'Lindqvist', 'Moreau', 'Rossi', 'Tanaka', 'Peña', 'Andersen', 'Kaya', 'Fischer', 'Costa', 'Brennan', 'Varga']


def rng_for(path):
    h = hashlib.sha256(('%d:%s' % (SEED, path)).encode('utf-8')).digest()
    return random.Random(int.from_bytes(h[:8], 'big'))


def noisy(r, s, p):
    """Letter-case / surrounding-space variant of s with probability p (F-main only)."""
    if r.random() >= p:
        return s
    k = r.randrange(6)
    return [s.upper(), s.lower(), ' ' + s, s + ' ', ' ' + s.lower() + ' ', s.upper() + '  '][k]


def f2(x):
    return '%.2f' % x


def pct(k, n):
    return int(round(100.0 * k / n)) if n else 0


# ---------------------------------------------------------------- New York local time (2025 rules, for offsets)
def ny_offset_2025(local):
    """UTC offset in hours of a New York wall-clock time in 2025 (DST 2025-03-09 02:00 to 2025-11-02 02:00)."""
    start = dt.datetime(2025, 3, 9, 2, 0)
    end = dt.datetime(2025, 11, 2, 2, 0)
    assert not (start <= local < start + dt.timedelta(hours=1)), local     # non-existent hour
    assert not (end - dt.timedelta(hours=1) <= local < end), local         # ambiguous hour
    return -4 if start <= local < end else -5


# ---------------------------------------------------------------- file builders
# Each builder returns dict(cols=[(name, kind)], clean=[[str]], main=[[str]], desc=callable(stats) -> str).
# 'clean' holds the true values; 'main' the same rows with F-main noise and missing cells ('' = empty cell).
BUILDERS = []


def builder(family, name):
    def deco(fn):
        BUILDERS.append((family, name, fn))
        return fn
    return deco


class Stats:
    def __init__(self, cols, main, clean):
        self.names = [c for c, _ in cols]
        self.main, self.clean, self.n = main, clean, len(main)

    def col(self, c, which='main'):
        i = self.names.index(c)
        return [row[i] for row in (self.main if which == 'main' else self.clean)]

    def empty(self, c):
        k = sum(1 for v in self.col(c) if v == '')
        assert k > 0, 'described as having empty cells but has none: %s' % c
        return pct(k, self.n)

    def count(self, c, val):
        k = sum(1 for v in self.col(c) if v == val)
        assert k > 0, (c, val)
        return pct(k, self.n)

    def noisy(self, c):
        k = sum(1 for a, b in zip(self.col(c), self.col(c, 'clean')) if a not in ('', '-') and a != b)
        assert k > 0, 'described as noisy but no noisy cell: %s' % c
        return k

    def no_empty(self, *cs):
        for c in cs:
            assert all(v != '' for v in self.col(c)), 'described as complete but has empty cells: %s' % c
        return ''


# ---------------- QF1_STRING
CITIES_A = ['Malmö', 'Zürich', 'Kraków', 'São Paulo', 'Lyon', 'Porto', 'Gdańsk', 'Bergen']


@builder('QF1_STRING', 'members.csv')
def b_members(r):
    cols = [('member_id', 'id'), ('full_name', 'text'), ('home_city', 'text'), ('fee', 'float')]
    clean, main = [], []
    for i in range(240):
        mid = str(5001 + i)
        name = '%s %s' % (r.choice(FIRST), r.choice(LAST))
        city = r.choice(CITIES_A)
        fee = f2(r.choice([120, 150, 180, 240]) - r.choice([0, 0, 0, 15.5, 22.25]))
        clean.append([mid, name, city, fee])
        u = r.random()
        mcity = '' if u < 0.05 else ('-' if u < 0.085 else noisy(r, city, 0.3))
        main.append([mid, noisy(r, name, 0.15), mcity, fee])

    def desc(s):
        s.no_empty('member_id', 'full_name', 'fee'); s.noisy('full_name'); s.noisy('home_city')
        return ('Club members, one per row (%d rows): member_id (whole number), full_name (first and last name; many '
                'names have accented letters; capital letters and spaces around the name are inconsistent), home_city '
                '(city name, several with accented letters; capital letters and spaces around the name are '
                'inconsistent; about %d%% of cells are empty and about %d%% hold "-" for an unknown city), fee (yearly '
                'fee, two decimals).' % (s.n, s.empty('home_city'), s.count('home_city', '-')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF1_STRING', 'branch_sales.csv')
def b_branch_sales(r):
    cols = [('branch_code', 'zpad'), ('week', 'int'), ('sales', 'int')]
    codes = sorted({'%05d' % r.randint(30, 9800) for _ in range(40)})[:12]
    assert len(codes) == 12 and all(c.startswith('0') for c in codes)
    clean, main = [], []
    for i in range(180):
        code = codes[r.randrange(12)]
        week = str(1 + i // 12)
        sales = str(r.randint(40, 950))
        clean.append([code, week, sales])
        main.append([code, week, '' if r.random() < 0.03 else sales])

    def desc(s):
        s.no_empty('branch_code', 'week')
        return ('Weekly sales per shop branch (%d rows): branch_code (five-digit branch code written with leading zeros, '
                'e.g. "%s"; 12 different branches, each appearing in many rows), week (week number 1-15), sales (units '
                'sold, whole number; about %d%% of cells are empty).' % (s.n, s.col('branch_code')[0], s.empty('sales')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF1_STRING', 'price_list.csv')
def b_price_list(r):
    cols = [('sku', 'text'), ('item', 'text'), ('section', 'cat'), ('price', 'float')]
    items = [('crème fraîche', 'dairy'), ('Gruyère', 'dairy'), ('skyr', 'dairy'), ('feta', 'dairy'),
             ('jalapeño salsa', 'pantry'), ('açaí bowl mix', 'pantry'), ('pâté', 'pantry'), ('muesli', 'pantry'),
             ('café crème beans', 'drinks'), ('rooibos', 'drinks'), ('cola', 'drinks'), ('kombucha', 'drinks'),
             ('brioche', 'bakery'), ('baguette', 'bakery'), ('pain au chocolat', 'bakery'), ('rye loaf', 'bakery')]
    sizes = ['small', 'medium', 'large', 'family']
    clean, main = [], []
    k = 0
    for name, sec in items:
        for sz in sizes:
            k += 1
            sku = 'PL-%04d' % (k * 7)
            item = '%s (%s)' % (name, sz)
            cents = r.randint(9, 240) * 10 + (0 if r.random() < 0.5 else r.randint(1, 9))
            price = '%d.%02d' % divmod(cents, 100)
            clean.append([sku, item, sec, price])
            main.append([sku, item, noisy(r, sec, 0.12), price])

    def desc(s):
        s.no_empty('sku', 'item', 'section', 'price'); s.noisy('section')
        n0 = sum(1 for v in s.col('price') if v.endswith('0'))
        assert n0 > 0
        return ('Shop price list (%d rows): sku (text code such as "PL-0007"), item (product name with size; several '
                'names have accented letters), section (dairy, pantry, drinks or bakery; capital letters and spaces '
                'are inconsistent), price (written with exactly two decimals, e.g. "%s"; no empty cells).'
                % (s.n, [v for v in s.col('price') if v.endswith('0')][0]))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


# ---------------- QF2_DATETIME
def rand_date(r, a, b):
    d0 = dt.date(*a); d1 = dt.date(*b)
    return d0 + dt.timedelta(days=r.randint(0, (d1 - d0).days))


@builder('QF2_DATETIME', 'signups.csv')
def b_signups(r):
    cols = [('account_id', 'id'), ('signup_day', 'date'), ('channel', 'cat'), ('first_payment', 'float')]
    clean, main = [], []
    for i in range(300):
        aid = str(70001 + i)
        day = rand_date(r, (2023, 1, 4), (2025, 12, 28)).isoformat()
        ch = r.choice(['web', 'app', 'referral', 'partner'])
        pay = f2(r.uniform(5, 95))
        clean.append([aid, day, ch, pay])
        u = r.random()
        main.append([aid, day, '' if u < 0.03 else noisy(r, ch, 0.15), '' if r.random() < 0.05 else pay])

    def desc(s):
        s.no_empty('account_id', 'signup_day'); s.noisy('channel')
        return ('Account sign-ups (%d rows, not in date order): account_id (whole number), signup_day (date as text, '
                'YYYY-MM-DD, between 2023 and 2025; no empty cells), channel (web, app, referral or partner; capital '
                'letters and spaces are inconsistent; about %d%% empty), first_payment (amount with two decimals; about '
                '%d%% empty).' % (s.n, s.empty('channel'), s.empty('first_payment')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF2_DATETIME', 'shipments.csv')
def b_shipments(r):
    cols = [('shipment_id', 'id'), ('ordered_on', 'date'), ('shipped_on', 'date'), ('carrier', 'cat'),
            ('weight_kg', 'float'), ('value', 'float')]
    clean, main = [], []
    for i in range(400):
        sid = str(300001 + i)
        od = rand_date(r, (2025, 1, 2), (2025, 12, 20))
        sd = (od + dt.timedelta(days=r.randint(0, 6))).isoformat()
        car = r.choice(['DHL', 'UPS', 'PostNord', 'GLS'])
        w = '%.1f' % r.uniform(0.2, 30)
        v = f2(r.uniform(8, 1200))
        clean.append([sid, od.isoformat(), sd, car, w, v])
        main.append([sid, od.isoformat(), '' if r.random() < 0.04 else sd, noisy(r, car, 0.1), w, v])

    def desc(s):
        s.no_empty('shipment_id', 'ordered_on', 'weight_kg', 'value'); s.noisy('carrier')
        return ('Shipments (%d rows): shipment_id (whole number), ordered_on and shipped_on (dates as text, YYYY-MM-DD, '
                'in 2025; shipped_on is empty for about %d%% of rows that have not shipped yet), carrier (DHL, UPS, '
                'PostNord or GLS; capital letters and spaces are inconsistent), weight_kg (one decimal), value (order '
                'value, two decimals).' % (s.n, s.empty('shipped_on')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF2_DATETIME', 'clicks.csv')
def b_clicks(r):
    cols = [('click_ref', 'zpad'), ('epoch_s', 'epoch'), ('epoch_ms', 'epoch'), ('page', 'cat'), ('dwell_s', 'float')]
    base = int(dt.datetime(2025, 4, 1, tzinfo=dt.timezone.utc).timestamp())
    clean, main = [], []
    for i in range(500):
        ref = '%07d' % (i * 37 + 11)
        es = base + r.randint(0, 120 * 86400)
        ems = es * 1000 + r.randint(5, 900)
        page = r.choice(['/home', '/pricing', '/docs', '/blog', '/signup'])
        dw = '%.1f' % r.uniform(0.5, 300)
        clean.append([ref, str(es), str(ems), page, dw])
        main.append([ref, str(es), str(ems), page, '' if r.random() < 0.06 else dw])

    def desc(s):
        s.no_empty('click_ref', 'epoch_s', 'epoch_ms', 'page')
        return ('Website clicks (%d rows): click_ref (seven-digit reference with leading zeros, e.g. "%s"), epoch_s '
                '(Unix timestamp in seconds, UTC, whole number), epoch_ms (Unix timestamp in milliseconds, UTC, when the '
                'click was received, whole number), page (site path such as /home or /pricing), dwell_s (seconds on '
                'the page, one decimal; about %d%% empty).' % (s.n, s.col('click_ref')[0], s.empty('dwell_s')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF2_DATETIME', 'appointments.csv')
def b_appointments(r):
    cols = [('appt_id', 'id'), ('local_start', 'datetime'), ('start_with_offset', 'dt_offset'), ('clinic', 'cat'),
            ('duration_min', 'int')]
    clean, main = [], []
    for i in range(160):
        u = r.random()
        if u < 0.25:
            d = dt.date(2025, 3, 8)
        elif u < 0.5:
            d = dt.date(2025, 11, 1)
        else:
            d = rand_date(r, (2025, 2, 17), (2025, 11, 28))
        t = dt.time(r.randint(8, 18), r.choice([0, 15, 30, 45]))
        loc = dt.datetime.combine(d, t)
        off = ny_offset_2025(loc)
        iso = loc.strftime('%Y-%m-%dT%H:%M:00') + ('%+03d:00' % off)
        clinic = r.choice(['Harbor', 'Midtown', 'Riverside'])
        dur = str(r.choice([15, 20, 30, 45, 60]))
        clean.append([str(101 + i), loc.strftime('%Y-%m-%d %H:%M'), iso, clinic, dur])
        main.append([str(101 + i), loc.strftime('%Y-%m-%d %H:%M'), iso, noisy(r, clinic, 0.12),
                     '' if r.random() < 0.04 else dur])

    def desc(s):
        s.no_empty('appt_id', 'local_start', 'start_with_offset'); s.noisy('clinic')
        offs = sorted({v[-6:] for v in s.col('start_with_offset')})
        assert offs == ['-04:00', '-05:00'], offs
        return ('Clinic appointments in New York (%d rows, February to November 2025, so the clock changes in March and '
                'November fall inside the data): appt_id (whole number), local_start (New York wall-clock start, text '
                'YYYY-MM-DD HH:MM, no UTC offset), start_with_offset (the same moment as ISO text with its UTC offset, '
                'e.g. "%s"), clinic (Harbor, Midtown or Riverside; capital letters and spaces are inconsistent), '
                'duration_min (whole minutes; about %d%% empty).' % (s.n, s.col('start_with_offset')[0],
                                                                       s.empty('duration_min')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF2_DATETIME', 'quarterly_revenue.csv')
def b_quarterly(r):
    cols = [('quarter_start', 'date'), ('revenue', 'int'), ('new_accounts', 'int')]
    rows = []
    y, m = 2019, 1
    for i in range(30):
        rows.append([dt.date(y, m, 1).isoformat(), str(r.randint(800, 2400) * 100), str(r.randint(40, 400))])
        m += 3
        if m > 12:
            y, m = y + 1, m - 12
    main = [list(x) for x in rows]

    def desc(s):
        s.no_empty('quarter_start', 'revenue', 'new_accounts')
        return ('Company revenue per calendar quarter (%d rows, oldest first, one row per quarter with no gaps): '
                'quarter_start (first day of the quarter as text, YYYY-MM-DD, from %s to %s), revenue (whole number), '
                'new_accounts (whole number).' % (s.n, s.col('quarter_start')[0], s.col('quarter_start')[-1]))
    return dict(cols=cols, clean=rows, main=main, desc=desc)


@builder('QF2_DATETIME', 'sessions.csv')
def b_sessions(r):
    cols = [('session_id', 'id'), ('user_code', 'zpad'), ('started_at', 'datetime'), ('pages_viewed', 'int'),
            ('device', 'cat')]
    clean, main = [], []
    t0 = dt.datetime(2025, 6, 1)
    for i in range(250):
        st = t0 + dt.timedelta(seconds=r.randint(0, 29 * 86400))
        uc = '%05d' % r.randint(1, 4000)
        pv = str(r.randint(1, 40))
        dev = r.choice(['desktop', 'mobile', 'tablet'])
        clean.append([str(9001 + i), uc, st.strftime('%Y-%m-%d %H:%M:%S'), pv, dev])
        main.append([str(9001 + i), uc, st.strftime('%Y-%m-%d %H:%M:%S'), '' if r.random() < 0.03 else pv,
                     noisy(r, dev, 0.1)])
    first = min(range(250), key=lambda k: clean[k][2])
    assert first != 0

    def desc(s):
        s.no_empty('session_id', 'user_code', 'started_at'); s.noisy('device')
        return ('Website sessions in June 2025 (%d rows, not in time order): session_id (whole number), user_code '
                '(five-digit code with leading zeros), started_at (timestamp written as YYYY-MM-DD HH:MM:SS; no empty '
                'cells), pages_viewed (whole number; about %d%% empty), device (desktop, mobile or tablet; capital '
                'letters and spaces are inconsistent).' % (s.n, s.empty('pages_viewed')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


# ---------------- QF3_COW
@builder('QF3_COW', 'bookings.csv')
def b_bookings(r):
    cols = [('booking_id', 'id'), ('state', 'cat'), ('total', 'float'), ('nights', 'int')]
    clean, main = [], []
    for i in range(300):
        st = r.choices(['paid', 'cancelled', 'refunded', 'pending'], [60, 15, 10, 15])[0]
        amt = r.uniform(80, 900)
        tot = f2(-amt if st == 'refunded' else amt)
        n = str(r.randint(1, 14))
        clean.append([str(40001 + i), st, tot, n])
        main.append([str(40001 + i), noisy(r, st, 0.1), tot, '' if r.random() < 0.03 else n])

    def desc(s):
        s.no_empty('booking_id', 'state', 'total'); s.noisy('state')
        neg = sum(1 for v in s.col('total') if v.startswith('-'))
        assert neg > 0
        return ('Hotel bookings (%d rows): booking_id (whole number), state (paid, cancelled, refunded or pending; '
                'mostly lower case, some with other capitals or extra spaces), total (booking amount, two decimals; '
                'refunded bookings are negative), nights (whole number; about %d%% empty).' % (s.n, s.empty('nights')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF3_COW', 'admissions.csv')
def b_admissions(r):
    cols = [('admission_id', 'id'), ('age', 'int'), ('ward', 'cat'), ('stay_days', 'int'), ('charge', 'float')]
    clean, main = [], []
    for i in range(260):
        age = str(r.randint(18, 95))
        ward = r.choice(['cardiology', 'oncology', 'maternity', 'orthopedics', 'neurology'])
        stay = str(r.randint(1, 21))
        ch = f2(r.uniform(400, 9000))
        clean.append([str(600 + i), age, ward, stay, ch])
        main.append([str(600 + i), '' if r.random() < 0.06 else age, noisy(r, ward, 0.1),
                     '' if r.random() < 0.04 else stay, '' if r.random() < 0.05 else ch])

    def desc(s):
        s.no_empty('admission_id', 'ward'); s.noisy('ward')
        return ('Hospital admissions (%d rows): admission_id (whole number), age (years, whole number; about %d%% empty), '
                'ward (cardiology, oncology, maternity, orthopedics or neurology; capital letters and spaces are '
                'inconsistent), stay_days (whole number; about %d%% empty), charge (two decimals; about %d%% empty).'
                % (s.n, s.empty('age'), s.empty('stay_days'), s.empty('charge')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF3_COW', 'gauges.csv')
def b_gauges(r):
    cols = [('gauge', 'text'), ('reading', 'float'), ('level', 'int'), ('site', 'cat')]
    clean, main = [], []
    for i in range(120):
        site = r.choice(['dam', 'canal', 'lake'])
        g = '%s-%02d' % (site[:2].upper(), i % 40 + 1)
        rd = '%.3f' % r.uniform(0.5, 9.5)
        lv = str(r.randint(3, 80))
        clean.append([g, rd, lv, site])
        main.append([g, rd if i == 0 or r.random() >= 0.03 else '', lv, noisy(r, site, 0.12)])

    def desc(s):
        s.no_empty('gauge', 'level', 'site'); s.noisy('site')
        return ('Water gauge log (%d rows): gauge (gauge name such as "%s"), reading (meters, three decimals; about %d%% '
                'empty), level (alert level, whole number from 3 to 80, no empty cells), site (dam, canal or lake; capital '
                'letters and spaces are inconsistent).' % (s.n, s.col('gauge')[0], s.empty('reading')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


# ---------------- QF4_GROUPBY
CITIES_B = ['Lisbon', 'Valencia', 'Nantes', 'Graz', 'Turku', 'Bilbao']


@builder('QF4_GROUPBY', 'subscribers.csv')
def b_subscribers(r):
    cols = [('subscriber_id', 'id'), ('age', 'int'), ('tier', 'cat'), ('monthly_fee', 'float'), ('joined_year', 'int')]
    fee = {'basic': 9.0, 'plus': 15.0, 'premium': 24.0}
    clean, main = [], []
    for i in range(320):
        age = str(r.randint(19, 87))
        tier = r.choices(['basic', 'plus', 'premium'], [50, 30, 20])[0]
        mf = f2(fee[tier] + r.choice([0, 0, 1.5, 3.0, -2.0]))
        jy = str(r.randint(2016, 2025))
        clean.append([str(2001 + i), age, tier, mf, jy])
        main.append([str(2001 + i), '' if r.random() < 0.03 else age, noisy(r, tier, 0.1),
                     '' if r.random() < 0.03 else mf, jy])

    def desc(s):
        s.no_empty('subscriber_id', 'tier', 'joined_year'); s.noisy('tier')
        ages = [int(v) for v in s.col('age') if v]
        return ('Streaming subscribers, one per row (%d rows): subscriber_id (whole number), age (years, from %d to %d; '
                'about %d%% empty), tier (basic, plus or premium; capital letters and spaces are inconsistent), '
                'monthly_fee (two decimals; about %d%% empty), joined_year (whole number).'
                % (s.n, min(ages), max(ages), s.empty('age'), s.empty('monthly_fee')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF4_GROUPBY', 'purchases.csv')
def b_purchases(r):
    cols = [('purchase_id', 'id'), ('subscriber_id', 'id'), ('store_city', 'text'), ('quantity', 'int'),
            ('spend', 'float')]
    clean, main = [], []
    for i in range(900):
        sub = str(2001 + r.randrange(320))
        city = r.choice(CITIES_B)
        q = r.randint(1, 6)
        sp = f2(q * r.uniform(3, 40))
        clean.append([str(800001 + i), sub, city, str(q), sp])
        main.append([str(800001 + i), sub, '' if r.random() < 0.02 else noisy(r, city, 0.3), str(q), sp])

    def desc(s):
        s.no_empty('purchase_id', 'subscriber_id', 'quantity', 'spend'); s.noisy('store_city')
        return ('Shop purchases (%d rows): purchase_id (whole number), subscriber_id (refers to subscribers.csv; most '
                'subscribers have several purchases), store_city (city name; the same city is written with different '
                'capitals and extra spaces, e.g. "lisbon" and "LISBON"; about %d%% empty), quantity (whole number), spend '
                '(two decimals).' % (s.n, s.empty('store_city')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF4_GROUPBY', 'unit_sales.csv')
def b_unit_sales(r):
    cols = [('region', 'cat'), ('channel', 'cat'), ('week', 'int'), ('units', 'int')]
    # Three regions only (FIX final run: a fourth region outside the label list of the G02 program made its 3.1 run
    # emit a pandas warning, unlike T2; see logs/fix/FIXTURE_CHANGES.md).
    combos = [(a, b) for a in ['north', 'south', 'west'] for b in ['online', 'store', 'kiosk']
              if (a, b) != ('west', 'kiosk')]
    clean, main = [], []
    for wk in range(1, 19):
        for a, b in combos:
            u = str(r.randint(0, 60))
            clean.append([a, b, str(wk), u])
            main.append([a, b, str(wk), '' if r.random() < 0.03 else u])

    def desc(s):
        s.no_empty('region', 'channel', 'week')
        return ('Weekly unit sales (%d rows): region (north, south or west), channel (online, store or kiosk; '
                'the west region has no kiosk, so that pair never occurs), week (week number 1-18), units (whole number; '
                'about %d%% empty).' % (s.n, s.empty('units')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


# ---------------- QF5_ORDER
def _footfall(r, days, other):
    cols = [('day', 'date'), ('visitors', 'int'), ('remark', 'text')]
    clean, main = [], []
    for d in days:
        v = str(r.choice([120, 140, 150, 150, 180, 200, 200, 220, 260]))
        rem = r.choice(['market day', 'rain', 'holiday', 'roadworks', 'quiet'])
        clean.append([d.isoformat(), v, rem])
        main.append([d.isoformat(), v, rem if r.random() < 0.4 else ''])
    return cols, clean, main


FOOT_DAYS = None


def foot_days():
    r = rng_for('QF5_ORDER/footfall_days')
    allday = [dt.date(2025, 9, 1) + dt.timedelta(days=k) for k in range(50)]
    north = r.sample(allday[:38], 36)
    south = r.sample(allday[12:], 36)
    return north, south


@builder('QF5_ORDER', 'footfall_north.csv')
def b_foot_n(r):
    cols, clean, main = _footfall(r, foot_days()[0], None)

    def desc(s):
        s.no_empty('day', 'visitors')
        return ('Daily visitor counts at the north entrance (%d rows, rows not in date order, each day at most once, '
                'some days missing): day (date as text, YYYY-MM-DD, September-October 2025), visitors (whole number; '
                'equal counts are common), remark (short note; about %d%% empty). The dates overlap only partly with '
                'footfall_south.csv.' % (s.n, s.empty('remark')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF5_ORDER', 'footfall_south.csv')
def b_foot_s(r):
    cols, clean, main = _footfall(r, foot_days()[1], None)

    def desc(s):
        s.no_empty('day', 'visitors')
        return ('Daily visitor counts at the south entrance (%d rows, rows not in date order, each day at most once, '
                'some days missing): day (date as text, YYYY-MM-DD, September-October 2025), visitors (whole number; '
                'equal counts are common), remark (short note; about %d%% empty). The dates overlap only partly with '
                'footfall_north.csv.' % (s.n, s.empty('remark')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


CITIES_C = ['Oslo', 'Rome', 'Ghent', 'Bern', 'Riga', 'Cork']


@builder('QF5_ORDER', 'memberships.csv')
def b_memberships(r):
    cols = [('member_ref', 'zpad'), ('plan', 'cat'), ('city', 'text'), ('points', 'int')]
    clean, main = [], []
    for i in range(200):
        plan = r.choices(['silver', 'gold', 'bronze', 'platinum'], [35, 20, 35, 10])[0]
        city = r.choice(CITIES_C)
        pts = str(r.randint(0, 40) * 50)
        clean.append(['%06d' % (i * 13 + 7), plan, city, pts])
        main.append(['%06d' % (i * 13 + 7), plan, noisy(r, city, 0.1), pts])
    seen = []
    for row in main:
        if (row[1], row[2]) not in seen:
            seen.append((row[1], row[2]))
    assert seen[:3] != sorted(seen)[:3]

    def desc(s):
        s.no_empty('member_ref', 'plan', 'city', 'points'); s.noisy('city')
        return ('Loyalty memberships (%d rows): member_ref (six-digit reference with leading zeros), plan (bronze, '
                'silver, gold or platinum), city (city name; capital letters and spaces are inconsistent in some rows), '
                'points (whole number, multiples of 50; many members share the same points).' % s.n)
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF5_ORDER', 'exam_scores.csv')
def b_exam(r):
    cols = [('student', 'text'), ('math', 'int'), ('art', 'int'), ('music', 'int')]
    names = []
    while len(names) < 60:
        nm = '%s %s' % (r.choice(FIRST), r.choice(LAST))
        if nm not in names:
            names.append(nm)
    clean, main = [], []
    for i, nm in enumerate(names):
        sc = [str(r.randint(35, 100)) for _ in range(3)]
        clean.append([nm] + sc)
        if i == 17:
            main.append([nm, '', '', ''])
        else:
            main.append([nm] + ['' if r.random() < 0.08 else v for v in sc])

    def desc(s):
        s.no_empty('student')
        allm = sum(1 for row in s.main if row[1:] == ['', '', ''])
        assert allm == 1
        return ('Exam scores (%d rows, one per student): student (full name, unique, many with accented letters), then '
                'math, art and music (scores 35-100, whole numbers; about %d%% of these score cells are empty, and one '
                'student has no score at all).' % (s.n, pct(sum(1 for row in s.main for v in row[1:] if v == ''),
                                                         3 * s.n)))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


def _returns(r, n, start_id):
    cols = [('return_id', 'id'), ('quantity', 'int'), ('refund', 'float')]
    clean, main = [], []
    for i in range(n):
        q = r.randint(1, 4)
        rf = f2(q * r.uniform(4, 60))
        clean.append([str(start_id + i), str(q), rf])
        main.append([str(start_id + i), str(q), rf])
    return cols, clean, main


@builder('QF5_ORDER', 'returns_march.csv')
def b_ret_mar(r):
    cols, clean, main = _returns(r, 80, 1)

    def desc(s):
        s.no_empty('return_id', 'quantity', 'refund')
        return ('Product returns in March (%d rows): return_id (whole number), quantity (whole number), refund (two '
                'decimals). Same columns as returns_april.csv.' % s.n)
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF5_ORDER', 'returns_april.csv')
def b_ret_apr(r):
    cols, clean, main = _returns(r, 0, 81)

    def desc(s):
        assert s.n == 0
        return ('Product returns in April: the header row (return_id, quantity, refund, as in returns_march.csv) and '
                'no data rows, because nothing was returned in April.')
    return dict(cols=cols, clean=clean, main=main, desc=desc)


# ---------------- QF6_NA_DTYPE
@builder('QF6_NA_DTYPE', 'deliveries.csv')
def b_deliveries(r):
    cols = [('delivery_id', 'id'), ('city', 'text'), ('status', 'cat'), ('parcels', 'int'), ('express', 'bool')]
    clean, main = [], []
    for i in range(240):
        city = r.choice(CITIES_C)
        st = r.choices(['shipped', 'pending'], [70, 30])[0]
        p = str(r.randint(1, 9))
        ex = r.choice(['True', 'False', 'False'])
        clean.append([str(1 + i), city, st, p, ex])
        main.append([str(1 + i), noisy(r, city, 0.15), st, '' if r.random() < 0.04 else p,
                     '' if r.random() < 0.05 else ex])

    def desc(s):
        s.no_empty('delivery_id', 'city', 'status'); s.noisy('city')
        assert set(s.col('status')) == {'shipped', 'pending'}
        return ('Parcel deliveries (%d rows): delivery_id (whole number), city (city name; capital letters and spaces '
                'are inconsistent), status (exactly "shipped" or "pending", always lower case, no empty cells), parcels '
                '(whole number; about %d%% empty), express (True or False; about %d%% empty).'
                % (s.n, s.empty('parcels'), s.empty('express')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF6_NA_DTYPE', 'store_traffic.csv')
def b_store_traffic(r):
    cols = [('store', 'text'), ('sales', 'int'), ('visits', 'int'), ('open_sunday', 'bool')]
    clean, main = [], []
    zz = {5, 33, 61}           # rows with no visits and no sales
    for i in range(90):
        st = 'Store %02d' % (i % 30 + 1)
        if i in zz:
            sa, vi = 0, 0
        else:
            vi = r.randint(3, 400)
            sa = r.randint(1, 60) if i % 9 else 0
        os_ = r.choice(['True', 'False'])
        clean.append([st, str(sa), str(vi), os_])
        main.append([st, str(sa), '' if (i not in zz and r.random() < 0.05) else str(vi),
                     '' if r.random() < 0.05 else os_])

    def desc(s):
        s.no_empty('store', 'sales')
        both0 = sum(1 for row in s.main if row[1] == '0' and row[2] == '0')
        assert both0 > 0
        return ('Daily store traffic (%d rows): store (name such as "Store 07"), sales (whole number of sales, zero on '
                'some days), visits (whole number of visits, zero on some days; about %d%% empty), open_sunday (True or '
                'False; about %d%% empty).' % (s.n, s.empty('visits'), s.empty('open_sunday')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF6_NA_DTYPE', 'quiz_scores.csv')
def b_quiz(r):
    # Only the two score columns (FIX run 1: an extra seat column made the N05 comparison raise on 2.3.3; see
    # logs/fix/FIXTURE_CHANGES.md). Rows are in seat order, so the row position is the seat.
    cols = [('quiz_a', 'int'), ('quiz_b', 'int')]
    clean, main = [], []
    for i in range(80):
        a, b = str(r.randint(0, 10)), str(r.randint(0, 10))
        clean.append([a, b])
        main.append(['' if r.random() < 0.08 else a, '' if r.random() < 0.08 else b])

    def desc(s):
        return ('Quiz results (%d rows, one per student in seat order, no other columns): quiz_a and quiz_b (points '
                '0-10, whole numbers, many equal values; about %d%% and %d%% of cells empty for absent students).'
                % (s.n, s.empty('quiz_a'), s.empty('quiz_b')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


# ---------------- QF7_INDEX_REDUCE
PRODUCTS = ['kettle', 'toaster', 'blender', 'lamp', 'fan', 'heater', 'mixer', 'grill', 'iron', 'scale']


@builder('QF7_INDEX_REDUCE', 'order_lines.csv')
def b_order_lines(r):
    cols = [('line_id', 'id'), ('product', 'text'), ('quantity', 'int'), ('amount', 'float')]
    clean, main = [], []
    for i in range(300):
        p = r.choice(PRODUCTS)
        q = r.randint(1, 8)
        a = f2(q * r.uniform(9, 120))
        clean.append([str(1 + i), p, str(q), a])
        main.append([str(1 + i), noisy(r, p, 0.08), '' if r.random() < 0.03 else str(q),
                     '' if r.random() < 0.03 else a])

    def desc(s):
        s.no_empty('line_id', 'product'); s.noisy('product')
        return ('Order lines (%d rows): line_id (whole number), product (product name; capital letters and spaces are '
                'inconsistent), quantity (whole number; about %d%% empty), amount (line total, two decimals; about %d%% '
                'empty).' % (s.n, s.empty('quantity'), s.empty('amount')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF7_INDEX_REDUCE', 'code_changes.csv')
def b_code_changes(r):
    cols = [('product', 'text'), ('stock_qty', 'int'), ('old_code', 'int'), ('new_code', 'int')]
    clean, main = [], []
    for i in range(150):
        p = '%s %s' % (r.choice(PRODUCTS), r.choice(['mini', 'pro', 'max', 'eco', 'plus']))
        oc = r.randint(1000, 9999)
        nc = oc if r.random() < 0.6 else r.randint(1000, 9999)
        q = str(r.randint(0, 250))
        clean.append([p, q, str(oc), str(nc)])
        main.append([p, q, str(oc), str(nc)])

    def desc(s):
        s.no_empty('product', 'stock_qty', 'old_code', 'new_code')
        same = sum(1 for row in s.main if row[2] == row[3])
        return ('Product code changes (%d rows): product (name with model), stock_qty (whole number), old_code and '
                'new_code (four-digit whole numbers; the code is unchanged in %d rows). No empty cells.' % (s.n, same))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF7_INDEX_REDUCE', 'parcel_rates.csv')
def b_parcel_rates(r):
    cols = [('weight_kg', 'float'), ('zones', 'int'), ('fee', 'float')]
    clean, main = [], []
    w = 0.0
    for i in range(120):
        w += r.choice([0.35, 0.4, 0.45, 0.5, 0.55])
        wk = '%.2f' % w
        if wk.endswith('.00'):
            wk = '%.2f' % (w + 0.05); w += 0.05
        z = str(r.randint(1, 5))
        fee = f2(3 + 0.9 * w + 1.5 * int(z))
        clean.append([wk, z, fee])
        main.append([wk, z, '' if r.random() < 0.03 else fee])
    ws = [float(row[0]) for row in clean]
    assert ws == sorted(ws) and len(set(ws)) == len(ws) and all(x != int(x) for x in ws)

    def desc(s):
        s.no_empty('weight_kg', 'zones')
        ws = [float(v) for v in s.col('weight_kg')]
        return ('Parcel price table (%d rows, sorted by weight_kg, each weight once): weight_kg (two decimals, from '
                '%.2f to %.2f, never a whole number), zones (whole number 1-5), fee (two decimals; about %d%% empty).'
                % (s.n, ws[0], ws[-1], s.empty('fee')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


INT64_MAX = 9223372036854775807


@builder('QF7_INDEX_REDUCE', 'storage_quota.csv')
def b_storage(r):
    cols = [('account_id', 'id'), ('active', 'bool'), ('quota_bytes', 'int'), ('used_bytes', 'int')]
    clean, main = [], []
    for i in range(150):
        unl = r.random() < 0.1 or i == 3
        q = INT64_MAX if unl else r.choice([5, 20, 100, 500]) * 1024 ** 3
        act = 'True' if (i == 3 or r.random() < 0.8) else 'False'
        used = r.randint(0, 5 * 1024 ** 3 if not unl else 900 * 1024 ** 3)
        clean.append([str(31 + i), act, str(q), str(used)])
        main.append([str(31 + i), act, str(q), str(used)])
    assert any(row[1] == 'True' and row[2] == str(INT64_MAX) for row in clean)

    def desc(s):
        s.no_empty('account_id', 'active', 'quota_bytes', 'used_bytes')
        k = sum(1 for v in s.col('quota_bytes') if v == str(INT64_MAX))
        return ('Cloud storage accounts (%d rows): account_id (whole number), active (True or False), quota_bytes '
                '(storage limit in bytes, whole number; the %d unlimited accounts carry the value %d), used_bytes (whole '
                'number). No empty cells.' % (s.n, k, INT64_MAX))
        # REPAIR 2026-11-11 (review SF1): ', the largest signed 64-bit integer' removed from the line above (it names the storage type)
    return dict(cols=cols, clean=clean, main=main, desc=desc)


# ---------------- QF8_NUMERIC
@builder('QF8_NUMERIC', 'daily_temps.csv')
def b_daily_temps(r):
    cols = [('date', 'date'), ('temp_c', 'float'), ('humidity', 'int')]
    clean, main = [], []
    for i in range(90):
        d = (dt.date(2025, 6, 1) + dt.timedelta(days=i)).isoformat()
        t = '%.2f' % (19 + 6 * r.random() + 0.04 * i)
        h = str(r.randint(35, 90))
        clean.append([d, t, h])
        main.append([d, '' if r.random() < 0.03 else t, h])

    def desc(s):
        s.no_empty('date', 'humidity')
        return ('Daily weather at one station (%d rows, one per day in date order from %s, no gaps): date (YYYY-MM-DD), '
                'temp_c (mean temperature in degrees C, two decimals; about %d%% empty), humidity (percent, whole '
                'number).' % (s.n, s.col('date')[0], s.empty('temp_c')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('QF8_NUMERIC', 'panel_scores.csv')
def b_panel_scores(r):
    cols = [('panel', 'cat'), ('entrant', 'text'), ('score', 'float')]
    clean, main = [], []
    panels = ['bread', 'cheese', 'cider', 'honey', 'jam', 'pickles', 'pies', 'soup']
    for p in panels:
        for j in range(12):
            e = '%s %s' % (r.choice(FIRST), r.choice(LAST))
            sc = '%.1f' % (r.randint(40, 100) / 10.0)
            clean.append([p, e, sc])
            main.append([p, noisy(r, e, 0.1), sc])

    def desc(s):
        s.no_empty('panel', 'entrant', 'score'); s.noisy('entrant')
        return ('Tasting competition scores (%d rows): panel (one of 8 panels, e.g. bread or cheese; 12 entrants each), '
                'entrant (person name; capital letters and spaces are inconsistent), score (4.0-10.0, one decimal; no '
                'empty cells).' % s.n)
    return dict(cols=cols, clean=clean, main=main, desc=desc)


# ---------------- GEN (strata R and A)
DISTRICTS = ['Old Town', 'Harbourside', 'Northgate', 'Eastfield', 'Riverbend', 'Southpark']


def station_codes():
    r = rng_for('GEN/station_codes')
    return sorted({'%04d' % r.randint(10, 990) for _ in range(80)})[:48]


def rider_ids():
    return ['%06d' % (4000 + 17 * i) for i in range(400)]


@builder('GEN', 'riders.csv')
def b_riders(r):
    cols = [('rider_id', 'zpad'), ('display_name', 'text'), ('home_district', 'cat'), ('membership', 'cat'),
            ('joined_on', 'date'), ('birth_year', 'int'), ('credit_balance', 'float')]
    clean, main = [], []
    for rid in rider_ids():
        nm = '%s %s' % (r.choice(FIRST), r.choice(LAST))
        dis = r.choice(DISTRICTS)
        mem = r.choices(['casual', 'monthly', 'annual'], [45, 35, 20])[0]
        jo = rand_date(r, (2021, 3, 1), (2025, 10, 31)).isoformat()
        by = str(r.randint(1948, 2007))
        cb = f2(r.uniform(-15, 120))
        clean.append([rid, nm, dis, mem, jo, by, cb])
        main.append([rid, noisy(r, nm, 0.12), noisy(r, dis, 0.15), noisy(r, mem, 0.08),
                     '' if r.random() < 0.03 else jo, '' if r.random() < 0.04 else by,
                     '' if r.random() < 0.05 else cb])

    def desc(s):
        s.no_empty('rider_id', 'display_name', 'home_district', 'membership')
        for c in ('display_name', 'home_district', 'membership'):
            s.noisy(c)
        return ('Bike-share riders, one per row (%d rows): rider_id (six-digit id with leading zeros), display_name '
                '(person name, some with accented letters), home_district (one of 6 districts such as "Old Town"), '
                'membership (casual, monthly or annual) - these three text columns have inconsistent capital letters '
                'and stray spaces; joined_on (date as text, YYYY-MM-DD; about %d%% empty), birth_year (whole number; '
                'about %d%% empty), credit_balance (two decimals, can be negative; about %d%% empty).'
                % (s.n, s.empty('joined_on'), s.empty('birth_year'), s.empty('credit_balance')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('GEN', 'stations.csv')
def b_stations(r):
    cols = [('station_code', 'zpad'), ('station_name', 'text'), ('district', 'cat'), ('docks', 'int'),
            ('opened_on', 'date')]
    names = ['Market Square', 'Ferry Pier', 'Library', 'Glassworks', 'Central Station', 'Café Müller', 'Old Mill',
             'Rosengård', 'Parkside', 'University', 'Museum', 'Fish Market', 'Brewery', 'Hospital', 'Stadium', 'Zoo']
    clean, main = [], []
    for k, code in enumerate(station_codes()):
        nm = '%s %s' % (names[k % 16], ['North', 'South', 'East'][k // 16])
        dis = DISTRICTS[(k * 5) % 6]
        dk = str(r.choice([12, 16, 20, 24, 30]))
        op = rand_date(r, (2015, 4, 1), (2024, 9, 30)).isoformat()
        clean.append([code, nm, dis, dk, op])
        main.append([code, nm, noisy(r, dis, 0.1), dk, op])

    def desc(s):
        s.no_empty('station_code', 'station_name', 'district', 'docks', 'opened_on'); s.noisy('district')
        return ('Bike-share stations (%d rows, one per station): station_code (four-digit code with leading zeros, '
                'e.g. "%s"), station_name (text, a few with accented letters), district (same 6 districts as '
                'riders.csv; capital letters and spaces are inconsistent), docks (whole number), opened_on (date as '
                'text, YYYY-MM-DD).' % (s.n, s.col('station_code')[0]))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('GEN', 'trips.csv')
def b_trips(r):
    cols = [('trip_id', 'id'), ('rider_id', 'zpad'), ('start_station', 'zpad'), ('end_station', 'zpad'),
            ('started_at', 'datetime'), ('duration_min', 'int'), ('distance_km', 'float'), ('fare', 'float'),
            ('payment', 'cat'), ('rating', 'int')]
    rids, scs = rider_ids(), station_codes()
    clean, main = [], []
    t0 = dt.datetime(2025, 9, 1, 5, 0)
    for i in range(1500):
        st = t0 + dt.timedelta(minutes=r.randint(0, 61 * 24 * 60 - 1))
        dur = r.randint(3, 75)
        dist = '%.2f' % (dur * r.uniform(0.12, 0.3))
        fare = f2(1.0 + 0.15 * dur)
        pay = r.choices(['card', 'app', 'cash'], [50, 40, 10])[0]
        rat = str(r.randint(1, 5))
        clean.append([str(100001 + i), r.choice(rids), r.choice(scs), r.choice(scs), st.strftime('%Y-%m-%d %H:%M'),
                      str(dur), dist, fare, pay, rat])
        row = list(clean[-1])
        row[5] = '' if r.random() < 0.02 else row[5]
        row[7] = '' if r.random() < 0.03 else row[7]
        row[8] = noisy(r, pay, 0.1)
        row[9] = '' if r.random() < 0.2 else rat
        main.append(row)

    def desc(s):
        # REPAIR 2026-11-11 (review MF7, check F5): started_at runs 2025-09-01 05:24 .. 2025-11-01 04:36, so the period is stated as
        # '1 September to 1 November 2025' (was 'September-October 2025', not fixture-true for 4 rows)
        s.no_empty('trip_id', 'rider_id', 'start_station', 'end_station', 'started_at', 'distance_km', 'payment')
        s.noisy('payment')
        return ('Bike-share trips, 1 September to 1 November 2025 (%d rows): trip_id (whole number), rider_id (refers to '
                'riders.csv), start_station and end_station (refer to station_code in stations.csv), started_at (timestamp '
                'written as YYYY-MM-DD HH:MM), duration_min (whole minutes; about %d%% empty), distance_km (two '
                'decimals), fare (two decimals; about %d%% empty), payment (card, app or cash; capital letters and '
                'spaces are inconsistent), rating (1-5 stars, whole number; about %d%% empty).'
                % (s.n, s.empty('duration_min'), s.empty('fare'), s.empty('rating')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('GEN', 'weather_hourly.csv')
def b_weather(r):
    cols = [('observed_at', 'datetime'), ('temp_c', 'float'), ('rain_mm', 'float'), ('wind_kmh', 'int'),
            ('sky', 'cat')]
    clean, main = [], []
    t0 = dt.datetime(2025, 9, 1, 0, 0)
    for h in range(30 * 24):
        t = t0 + dt.timedelta(hours=h)
        tc = '%.1f' % (14 + 6 * r.random() - 4 * abs(12 - t.hour) / 12.0)
        rain = '%.1f' % (0.0 if r.random() < 0.75 else r.uniform(0.1, 6))
        wind = str(r.randint(0, 45))
        sky = 'rain' if float(rain) > 0 else r.choice(['clear', 'cloudy', 'fog'])
        clean.append([t.strftime('%Y-%m-%d %H:%M'), tc, rain, wind, sky])
        main.append([t.strftime('%Y-%m-%d %H:%M'), '' if r.random() < 0.03 else tc, rain, wind, noisy(r, sky, 0.08)])

    def desc(s):
        s.no_empty('observed_at', 'rain_mm', 'wind_kmh', 'sky'); s.noisy('sky')
        return ('Hourly weather for the city, September 2025 (%d rows, one per hour in time order, no gaps): '
                'observed_at (timestamp written as YYYY-MM-DD HH:MM), temp_c (degrees C, one decimal; about %d%% '
                'empty), rain_mm (one decimal), wind_kmh (whole number), sky (clear, cloudy, fog or rain; capital '
                'letters and spaces are inconsistent).' % (s.n, s.empty('temp_c')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


@builder('GEN', 'fare_changes.csv')
def b_fare_changes(r):
    cols = [('station_code', 'zpad'), ('effective_from', 'date'), ('new_base_fare', 'float')]
    scs = station_codes()
    pick = sorted(r.sample(scs, 30))
    clean, main = [], []
    for sc in pick:
        ef = rand_date(r, (2025, 10, 1), (2025, 12, 31)).isoformat()
        nf = f2(r.choice([1.0, 1.2, 1.5, 1.8]))
        clean.append([sc, ef, nf])
        main.append([sc, ef, '' if r.random() < 0.07 else nf])

    def desc(s):
        s.no_empty('station_code', 'effective_from')
        return ('Planned fare changes (%d rows, one per affected station): station_code (refers to stations.csv; four '
                'digits with leading zeros), effective_from (date as text, YYYY-MM-DD), new_base_fare (two decimals; '
                'about %d%% empty).' % (s.n, s.empty('new_base_fare')))
    return dict(cols=cols, clean=clean, main=main, desc=desc)


# ---------------------------------------------------------------- confirmed row -> file map (for task authors)
ROW_FILES = [
    # id, files (relative to fixtures/<variant>/), columns the confirmation program uses on F-main
    ('S01', 'QF1_STRING/members.csv', 'home_city;fee;all text columns'),
    ('S02', 'QF1_STRING/members.csv', 'home_city'),
    ('S03', 'QF1_STRING/members.csv', 'home_city'),
    ('S06', 'QF1_STRING/branch_sales.csv', 'branch_code;sales'),
    ('O01', 'QF1_STRING/price_list.csv', 'price;all columns'),
    ('D01', 'QF2_DATETIME/signups.csv', 'account_id;signup_day'),
    ('D02', 'QF2_DATETIME/clicks.csv', 'epoch_s'),
    ('D03', 'QF2_DATETIME/shipments.csv', 'ordered_on;value'),
    ('D04', 'QF2_DATETIME/signups.csv', 'signup_day'),
    ('D05', 'QF2_DATETIME/appointments.csv', 'appt_id;local_start'),
    ('D06', 'QF2_DATETIME/appointments.csv', 'appt_id;local_start'),
    ('D07', 'QF2_DATETIME/clicks.csv', 'click_ref;epoch_s'),
    ('D08', 'QF2_DATETIME/shipments.csv', 'ordered_on;shipped_on;all columns'),
    ('D09', 'QF2_DATETIME/quarterly_revenue.csv', 'quarter_start'),
    ('D10', 'QF2_DATETIME/sessions.csv', 'started_at'),
    ('C01', 'QF3_COW/bookings.csv', 'state;total'),
    ('C02', 'QF3_COW/admissions.csv', 'age'),
    ('C03', 'QF3_COW/bookings.csv', 'total'),
    ('C04', 'QF3_COW/admissions.csv', 'all columns'),
    ('C05', 'QF3_COW/gauges.csv', 'reading (second column)'),
    ('C06', 'QF3_COW/gauges.csv', 'level'),
    ('G01', 'QF4_GROUPBY/subscribers.csv', 'age;monthly_fee'),
    ('G02', 'QF4_GROUPBY/unit_sales.csv', 'region;channel;units'),
    ('G03', 'QF4_GROUPBY/purchases.csv', 'subscriber_id;numeric columns'),
    ('G04', 'QF4_GROUPBY/purchases.csv', 'store_city;spend'),
    ('G05', 'QF4_GROUPBY/subscribers.csv', 'tier;monthly_fee'),
    ('G06', 'QF4_GROUPBY/subscribers.csv', 'tier;monthly_fee'),
    ('R01', 'QF5_ORDER/footfall_north.csv,QF5_ORDER/footfall_south.csv', 'day;visitors'),
    ('R02', 'QF5_ORDER/memberships.csv', 'plan;city'),
    ('R04', 'QF5_ORDER/exam_scores.csv', 'student;math;art;music'),
    ('R05', 'QF5_ORDER/returns_march.csv,QF5_ORDER/returns_april.csv', 'all columns'),
    ('N01', 'QF6_NA_DTYPE/deliveries.csv', 'city;status'),
    ('N02', 'QF6_NA_DTYPE/store_traffic.csv', 'sales;visits'),
    ('N05', 'QF6_NA_DTYPE/quiz_scores.csv', 'quiz_a;quiz_b'),
    ('N06', 'QF6_NA_DTYPE/quiz_scores.csv', 'quiz_a'),
    ('I01', 'QF7_INDEX_REDUCE/order_lines.csv', 'quantity;amount'),
    ('I02', 'QF7_INDEX_REDUCE/parcel_rates.csv', 'weight_kg;fee'),
    ('I05', 'QF7_INDEX_REDUCE/code_changes.csv', 'old_code;new_code'),
    ('I06', 'QF7_INDEX_REDUCE/storage_quota.csv', 'active;quota_bytes'),
    ('X01', 'QF8_NUMERIC/daily_temps.csv', 'temp_c'),
    ('X02', 'QF8_NUMERIC/panel_scores.csv', 'panel;score'),
]


# FULL_PREREG section 4.3 R paraphrase type table: generator kind -> fixture column type ('-' = not a target type)
PARAPHRASE_TYPE = {'text': 'general text', 'cat': 'category-like key', 'date': 'date-like text',
                   'datetime': 'date-like text', 'dt_offset': 'date-like text', 'int': 'integer numeric',
                   'float': 'float numeric', 'zpad': 'zero-padded id', 'id': '-', 'epoch': 'integer numeric',
                   'bool': '-'}


# ---------------------------------------------------------------- variants and output
def make_dirty(r, cols, main):
    """F-main plus about 5% '$'/'N/A' numeric cells (>= one '$' per numeric column) and a blank label per category column."""
    rows = [list(x) for x in main]
    n = len(rows)
    for j, (c, kind) in enumerate(cols):
        if n == 0:
            continue
        if kind in NUMERIC_KINDS:
            cand = [i for i in range(n) if rows[i][j] != '']
            if not cand:
                continue
            hit = [i for i in cand if r.random() < 0.05]
            dollar = False
            for i in hit:
                if r.random() < 0.5:
                    rows[i][j] = '$' + main[i][j]; dollar = True
                else:
                    rows[i][j] = 'N/A'
            if not dollar:      # every numeric column must read as text in F-dirty
                rest = [i for i in cand if i not in hit] or cand
                i = r.choice(rest)
                rows[i][j] = '$' + main[i][j]
        elif kind in CAT_KINDS:
            cand = list(range(n))
            k = max(1, int(round(0.02 * n)))
            for i in r.sample(cand, k):
                rows[i][j] = ' '
    return rows


def to_csv_bytes(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator='\n', quoting=csv.QUOTE_MINIMAL)
    w.writerow(header)
    for row in rows:
        w.writerow(row)
    return buf.getvalue().encode('utf-8')


def write_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, path)


def build_all():
    out = []
    for family, name, fn in BUILDERS:
        rel = '%s/%s' % (family, name)
        r = rng_for(rel)
        spec = fn(r)
        cols, clean, main = spec['cols'], spec['clean'], spec['main']
        assert len(clean) == len(main)
        for row in clean + main:
            assert len(row) == len(cols), rel
        dirty = make_dirty(rng_for(rel + '#dirty'), cols, main)
        desc = spec['desc'](Stats(cols, main, clean))
        out.append(dict(rel=rel, cols=cols, main=main, clean=clean, dirty=dirty, desc=desc))
    names = [o['rel'].split('/')[1] for o in out]
    assert len(names) == len(set(names)), 'basenames must be unique'
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description='Generate the study fixtures (F-main, F-clean, F-dirty).')
    ap.add_argument('--out', default=os.path.join(STUDY, 'fixtures'))
    a = ap.parse_args(argv)
    files = build_all()
    for o in files:
        header = [c for c, _ in o['cols']]
        for v in VARIANTS:
            write_bytes(os.path.join(a.out, v, o['rel']), to_csv_bytes(header, o[v]))
    lines = ['path\trows\tcolumns\tdescription']
    for o in files:
        assert '\t' not in o['desc'] and '\n' not in o['desc']
        lines.append('%s\t%d\t%d\t%s' % (o['rel'], len(o['main']), len(o['cols']), o['desc']))
    write_bytes(os.path.join(a.out, 'descriptions.tsv'), ('\n'.join(lines) + '\n').encode('utf-8'))
    lines = ['path\tcolumn\tkind\tparaphrase_type']
    for o in files:
        for c, k in o['cols']:
            lines.append('%s\t%s\t%s\t%s' % (o['rel'], c, k, PARAPHRASE_TYPE[k]))
    write_bytes(os.path.join(a.out, 'columns.tsv'), ('\n'.join(lines) + '\n').encode('utf-8'))
    lines = ['id\tfiles\tcolumns_used']
    for rid, fs, cu in ROW_FILES:
        lines.append('%s\t%s\t%s' % (rid, fs, cu))
    write_bytes(os.path.join(a.out, 'row_files.tsv'), ('\n'.join(lines) + '\n').encode('utf-8'))
    print('wrote %d files x %d variants under %s' % (len(files), len(VARIANTS), a.out))
    return 0


if __name__ == '__main__':
    sys.exit(main())
