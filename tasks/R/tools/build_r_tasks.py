"""Build the stratum-R tasks from the sealed intents (STAGE2 T4.2, T4.5; FULL_PREREG sections 4.3, 10.1; lead ruling LR10).

drafted_by: pkg:R_BUILD; status: prepared. Task text, intent summary and column map are taken VERBATIM from tasks/R/INTENTS.tsv; the build aborts unless
that file matches its seal (INTENTS_FROZEN.sha256, written 2026-11-11T13:44:13Z before the catalogue was opened).
Question id, URL, creation date, score and licence come from tasks/R/candidates.tsv (written by order_candidates.py from the API pages).
Cards are set from the task text alone under the card rule in force when the cards are built (FULL_PREREG section 3 with Amendment 3:
order_significant only for a sort, ranking, top-N or first/last by a stated key; the single flag rule LR2 is applied to all cards by the
next step, by script). Property-check numbers are F-main fixture facts computed here with the csv module; nothing uses any run output.
invited_ids_author were labelled in this step AFTER the intents were sealed, from the catalogue columns id, name and description
(SILENT rows only); intents are never rewritten for them.
Writes tasks/R/<id>/{task.json, reference.py} and tasks/R/mapping.tsv (no question text). Usage: python3 -I -B tasks/R/tools/build_r_tasks.py
"""
import csv, hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
S = os.path.abspath(os.path.join(PKG, '..', '..'))
INTENTS = os.path.join(PKG, 'INTENTS.tsv')
SEAL = os.path.join(PKG, 'INTENTS_FROZEN.sha256')
INTENTS_SHA = 'cb9177ce859bd996e33ad2aa676da549c37cdb2110c91c59cb2bdf8b58b72f9b'
DRAFTED_BY = 'pkg:R_BUILD'
STATUS = 'prepared'
NOTE = ('Stratum R (real question, paraphrased onto the general fixtures under the section 4.3 rule). Intent, summary and column map '
        'sealed 2026-11-11T13:44:13Z (tasks/R/INTENTS_FROZEN.sha256) before the catalogue was opened; card, reference and '
        'invited_ids_author drafted 2026-11-11 by pkg:R_BUILD. Prepared '
        '(Amendment 9). No question text or code is stored in the study folder.')


def load_intents():
    raw = open(INTENTS, 'rb').read()
    h = hashlib.sha256(raw).hexdigest()
    seal = open(SEAL, encoding='utf-8').read().split()[0]
    if h != INTENTS_SHA or seal != h:
        sys.exit('INTENTS.tsv does not match its seal: %s' % h)
    with open(INTENTS, encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def load_candidates():
    with open(os.path.join(PKG, 'candidates.tsv'), encoding='utf-8', newline='') as f:
        return {int(r['question_id']): r for r in csv.DictReader(f, delimiter='\t')}


def descriptions():
    with open(os.path.join(S, 'fixtures', 'descriptions.tsv'), encoding='utf-8') as f:
        return {r['path']: r['description'] for r in csv.DictReader(f, delimiter='\t')}


def rows(name):
    with open(os.path.join(S, 'fixtures', 'main', 'GEN', name), encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


RID, STA, TRP = rows('riders.csv'), rows('stations.csv'), rows('trips.csv')
N_RIDERS, N_TRIPS = len(RID), len(TRP)
DOCKS = [int(s['docks']) for s in STA]
BIRTH = [int(r['birth_year']) for r in RID if r['birth_year']]
DISTRICTS = sorted({r['home_district'].strip().lower() for r in RID})
N_LARGEST = max(sum(1 for r in RID if r['home_district'].strip().lower() == d) for d in DISTRICTS)
BLOCK_SUMS = [sum(int(r['birth_year']) for r in RID[i:i + 4] if r['birth_year']) for i in range(0, N_RIDERS, 4)]
N_RIDER_IDS_IN_TRIPS = len({t['rider_id'] for t in TRP})
GEN_CHECKS = [{'check': 'no_null_text', 'args': {}}, {'check': 'no_all_missing_column', 'args': {}}]


def pc(check, **args):
    return {'check': check, 'args': args}


IDS = 'id columns (rider_id, station codes) may be written as integers without leading zeros'
CARDS = {}

CARDS['R_01'] = dict(
 invited=['D01'], order=False, keys=[],
 intended='Read riders.csv and stations.csv; for each rider (file order kept or not) take the station with the latest opened_on <= '
 'joined_on (dates compared as dates; opened_on values are distinct) and attach its docks; riders with an empty joined_on or with no '
 'such station get a missing docks; columns joined_on, birth_year, docks; 400 rows.',
 notes='joined_on may be text or timestamps; birth_year and docks may be float with NaN or nullable integers; row order free',
 checks=[pc('n_groups_equals', n=N_RIDERS), pc('columns_present', columns=['joined_on', 'birth_year', 'docks']),
         pc('numeric_in_range', columns=['docks'], min=min(DOCKS), max=max(DOCKS)),
         pc('date_year_in_range', columns=['joined_on'], min_year=2021, max_year=2025)],
 ref=r'''import csv
import pandas as pd

with open('stations.csv', encoding='utf-8', newline='') as f:
    stations = sorted((r['opened_on'], int(r['docks'])) for r in csv.DictReader(f))
with open('riders.csv', encoding='utf-8', newline='') as f:
    riders = list(csv.DictReader(f))
joined, birth, docks = [], [], []
for r in riders:
    j = r['joined_on'].strip()
    d = None
    if j:
        before = [dk for opened, dk in stations if opened <= j]
        d = float(before[-1]) if before else None
    joined.append(j if j else None)
    birth.append(float(r['birth_year']) if r['birth_year'].strip() else None)
    docks.append(d)
result = pd.DataFrame({'joined_on': joined, 'birth_year': pd.Series(birth, dtype='float64'),
                       'docks': pd.Series(docks, dtype='float64')})
''')

CARDS['R_02'] = dict(
 invited=['G07'], order=False, keys=[],
 intended='Read riders.csv; birth_year in file order cut into 100 consecutive blocks of 4 rows; sum of the non-empty values of each '
 'block; 100 sums in block order.',
 notes='result may be a Series, list or one-column table; sums may be float',
 checks=[pc('n_groups_equals', n=len(BLOCK_SUMS)), pc('no_nulls', columns=['__values__']),
         pc('numeric_in_range', columns=['__values__'], min=min(BLOCK_SUMS), max=max(BLOCK_SUMS))],
 ref=r'''import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    years = [int(r['birth_year']) if r['birth_year'].strip() else None for r in csv.DictReader(f)]
sums = [sum(v for v in years[i:i + 4] if v is not None) for i in range(0, len(years), 4)]
result = pd.Series(sums, dtype='int64')
''')

CARDS['R_03'] = dict(
 invited=['N01'], order=False, keys=[],
 intended='Read trips.csv and stations.csv; map every start_station and end_station code through station_code -> docks (all codes '
 'are found); columns start_station, end_station holding docks numbers; 1500 rows.',
 notes='values may be int, float or text digits; row order free',
 checks=[pc('n_groups_equals', n=N_TRIPS), pc('columns_present', columns=['start_station', 'end_station']),
         pc('no_nulls', columns=['start_station', 'end_station']),
         pc('numeric_in_range', columns=['start_station', 'end_station'], min=min(DOCKS), max=max(DOCKS))],
 ref=r'''import csv
import pandas as pd

with open('stations.csv', encoding='utf-8', newline='') as f:
    lookup = {r['station_code']: int(r['docks']) for r in csv.DictReader(f)}
with open('trips.csv', encoding='utf-8', newline='') as f:
    trips = list(csv.DictReader(f))
result = pd.DataFrame({'start_station': [lookup.get(t['start_station'], t['start_station']) for t in trips],
                       'end_station': [lookup.get(t['end_station'], t['end_station']) for t in trips]})
''')

CARDS['R_04'] = dict(
 invited=['D01', 'C01'], order=False, keys=[],
 intended='Read trips.csv; parse started_at; subtract one hour from the trips whose started_at date is 2025-09-02 or 2025-09-03 '
 '(47 trips); all other values unchanged; one timestamp per trip in file order.',
 notes='result may be a Series or one-column table; the timestamps may be text in the same format',
 checks=[pc('n_groups_equals', n=N_TRIPS), pc('no_nulls', columns=['__values__']),
         pc('date_year_in_range', columns=['__values__'], min_year=2025, max_year=2025)],
 ref=r'''import csv
from datetime import datetime, timedelta
import pandas as pd

with open('trips.csv', encoding='utf-8', newline='') as f:
    raw = [r['started_at'] for r in csv.DictReader(f)]
out = []
for s in raw:
    t = datetime.strptime(s, '%Y-%m-%d %H:%M')
    if s[:10] in ('2025-09-02', '2025-09-03'):
        t = t - timedelta(hours=1)
    out.append(t)
result = pd.Series(pd.to_datetime(out), name='started_at')
''')

CARDS['R_05'] = dict(
 invited=['R06'], order=False, keys=[],
 intended='Read riders.csv; district = home_district stripped and lower-cased (6 values); columns = districts in alphabetical order; '
 'column d lists the birth_year values of the riders of d in file order (empty birth_year kept as a missing cell), padded with '
 'missing cells to %d rows (the largest district).' % N_LARGEST,
 notes='values may be float or nullable integers; the index may be 0..n-1 or unnamed',
 checks=[pc('n_groups_equals', n=N_LARGEST), pc('columns_present', columns=DISTRICTS),
         pc('numeric_in_range', columns=DISTRICTS, min=min(BIRTH), max=max(BIRTH))],
 ref=r'''import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    riders = list(csv.DictReader(f))
cols = {}
for r in riders:
    d = r['home_district'].strip().lower()
    cols.setdefault(d, []).append(float(r['birth_year']) if r['birth_year'].strip() else None)
n = max(len(v) for v in cols.values())
result = pd.DataFrame({d: pd.Series(cols[d] + [None] * (n - len(cols[d])), dtype='float64') for d in sorted(cols)})
''')

CARDS['R_06'] = dict(
 invited=[], order=False, keys=[],
 intended='Read riders.csv; b = birth_year in file order; change_k[i] = 1 - b[i-k] / b[i] for k = 1..4, missing when i < k or either '
 'value is empty; columns birth_year, change_1..change_4; 400 rows in file order.',
 notes='values may be rounded to 6 significant digits; birth_year may be float',
 checks=[pc('n_groups_equals', n=N_RIDERS),
         pc('columns_present', columns=['birth_year', 'change_1', 'change_2', 'change_3', 'change_4']),
         pc('numeric_in_range', columns=['change_1', 'change_2', 'change_3', 'change_4'], min=-1, max=1)],
 ref=r'''import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    b = [float(r['birth_year']) if r['birth_year'].strip() else None for r in csv.DictReader(f)]
data = {'birth_year': pd.Series(b, dtype='float64')}
for k in range(1, 5):
    col = []
    for i, v in enumerate(b):
        p = b[i - k] if i >= k else None
        col.append(1.0 - p / v if (p is not None and v is not None) else None)
    data['change_%d' % k] = pd.Series(col, dtype='float64')
result = pd.DataFrame(data)
''')

CARDS['R_07'] = dict(
 invited=[], order=False, keys=[],
 intended='Read riders.csv; b = birth_year in file order; value[i] = b[i] & b[i-1] (bitwise AND of the two whole numbers), missing '
 'for i = 0 or when either value is empty; 400 values in file order.',
 notes='values may be float, nullable integers or a list; missing may be NaN/None/NA',
 checks=[pc('n_groups_equals', n=N_RIDERS), pc('numeric_in_range', columns=['__values__'], min=0, max=max(BIRTH))],
 ref=r'''import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    b = [int(r['birth_year']) if r['birth_year'].strip() else None for r in csv.DictReader(f)]
out = [None] + [float(b[i] & b[i - 1]) if (b[i] is not None and b[i - 1] is not None) else None for i in range(1, len(b))]
result = pd.Series(out, dtype='float64')
''')

CARDS['R_08'] = dict(
 invited=[], order=False, keys=[],
 intended='Read riders.csv; d = home_district stripped and lower-cased, in file order; flag[i] = (i > 0 and d[i] == "harbourside" '
 'and d[i-1] == "riverbend"); 400 booleans in file order.',
 notes='flags may be booleans, 0/1 or a list',
 checks=[pc('n_groups_equals', n=N_RIDERS), pc('no_nulls', columns=['__values__']),
         pc('values_in_set', column='__values__', values=[True, False])],
 ref=r'''import csv
import pandas as pd

with open('riders.csv', encoding='utf-8', newline='') as f:
    d = [r['home_district'].strip().lower() for r in csv.DictReader(f)]
result = pd.Series([i > 0 and d[i] == 'harbourside' and d[i - 1] == 'riverbend' for i in range(len(d))], dtype='bool')
''')

CARDS['R_09'] = dict(
 invited=['G07'], order=False, keys=[],
 intended='Read trips.csv; total = sum of distance_km (no empty cells); row_count = 1500; per_rider = sum of distance_km per rider_id '
 '(%d rider ids); dict with keys total, row_count, per_rider.' % N_RIDER_IDS_IN_TRIPS,
 notes=IDS + '; per_rider may be a Series, dict or table; totals may differ in the last digits by summation order',
 checks=[pc('result_kind', kind='other')],
 ref=r'''import csv
import pandas as pd

with open('trips.csv', encoding='utf-8', newline='') as f:
    trips = list(csv.DictReader(f))
cents = [int(round(float(t['distance_km']) * 100)) for t in trips]
per = {}
for t, c in zip(trips, cents):
    per[t['rider_id']] = per.get(t['rider_id'], 0) + c
ids = sorted(per)
result = {'total': sum(cents) / 100, 'row_count': len(trips),
          'per_rider': pd.Series([per[i] / 100 for i in ids], index=pd.Index(ids, name='rider_id'), name='distance_km',
                                 dtype='float64')}
''')


def main():
    intents = load_intents()
    cand = load_candidates()
    desc = descriptions()
    mlines = ['id\tso_question_id\tso_url\tso_creation_date\tso_score\tso_licence\tintent_summary\tcolumn_map']
    for it in intents:
        tid, qid = it['id'], int(it['so_question_id'])
        c, card, files = cand[qid], CARDS[tid], it['files'].split(',')
        assert c['licence'] == 'CC BY-SA 4.0' and c['crit3_not_pilot'] == 'pass'
        task = {
            'id': tid, 'stratum': 'R', 'family': None, 'generic_family': None, 'catalogue_row': None,
            'files': [{'path': p, 'description': desc[p]} for p in files],
            'task_text': it['task_text'], 'allowed_task_words': [], 'invited_ids_author': card['invited'],
            'order_significant': card['order'], 'sort_keys': card['keys'], 'dtype_significant': False,
            'intended_computation': card['intended'],
            'acceptable_variants': {'row_order': 'ties_only' if card['order'] else 'any', 'label_spelling': True,
                                    'missing_value_representation': True, 'rounding_sig_digits': 6, 'notes': card['notes']},
            'property_checks': GEN_CHECKS + card['checks'],
            'predicted_direction': None, 'naive_path': None, 'reference_path': 'reference.py',
            'so_question_id': qid, 'so_url': 'https://stackoverflow.com/q/%d' % qid, 'so_creation_date': c['creation_utc'][:10],
            'so_score': int(c['score']), 'so_licence': 'CC BY-SA 4.0', 'intent_summary': it['intent_summary'],
            'column_map': json.loads(it['column_map']),
            'invitation_strength': None, 'invited_ids_reviewer': None, 'fidelity': None, 'independent_card_ref': None,
            'blind_provenance': None, 'drafted_by': DRAFTED_BY, 'status': STATUS, 'notes': NOTE}
        d = os.path.join(PKG, tid)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'task.json'), 'w', encoding='utf-8') as f:
            json.dump(task, f, indent=1, ensure_ascii=False)
            f.write('\n')
        with open(os.path.join(d, 'reference.py'), 'w', encoding='utf-8') as f:
            f.write('# Reference solution for %s (stratum R, question %d). drafted_by: %s; status: %s.\n# Written 2026-11-11 to give the '
                    'same canonical result on E0a, E0pa, E1, E2, E3 and E4 (csv module, results built from Python lists).\n'
                    % (tid, qid, DRAFTED_BY, STATUS) + card['ref'])
        mlines.append('\t'.join([tid, str(qid), task['so_url'], task['so_creation_date'], c['score'], 'CC BY-SA 4.0',
                                 it['intent_summary'], it['column_map']]))
    with open(os.path.join(PKG, 'mapping.tsv'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(mlines) + '\n')
    print('built %d R tasks' % len(intents))


if __name__ == '__main__':
    main()
