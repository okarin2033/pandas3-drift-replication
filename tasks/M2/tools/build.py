# Build the stratum-M task folders of package TASKS_M2 (QF5-QF8) from the spec modules in this folder.
# Written 2026-11-11 by pkg:TASKS_M2. Standard library only; run from anywhere:  python3 -I -B tasks/M2/tools/build.py [--only ID ...]
# Writes tasks/M2/<id>/task.json (CONVENTIONS 5; schema task.schema.json), naive.py and reference.py. Descriptions are copied
# verbatim from fixtures/descriptions.tsv. Overwrites existing folders of the listed ids (rewrites are logged by hand in logs/).
import argparse, csv, json, os, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(TOOLS)
STUDY = os.path.dirname(os.path.dirname(PKG))
sys.path.insert(0, TOOLS)

FAMILY = {'QF5': 'QF5_ORDER', 'QF6': 'QF6_NA_DTYPE', 'QF7': 'QF7_INDEX_REDUCE', 'QF8': 'QF8_NUMERIC'}
DRAFT = 'prepared'
DATE = '2026-11-11'


def load_specs():
    specs = []
    for mod in ('specs_qf5', 'specs_qf6', 'specs_qf7', 'specs_qf8'):
        if os.path.exists(os.path.join(TOOLS, mod + '.py')):
            specs += __import__(mod).SPECS
    ids = [s['id'] for s in specs]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        raise SystemExit('duplicate spec ids: %s' % dup)
    return specs


def descriptions():
    with open(os.path.join(STUDY, 'fixtures', 'descriptions.tsv'), encoding='utf-8', newline='') as f:
        return {r['path']: r['description'] for r in csv.DictReader(f, delimiter='\t')}


def task_json(s, desc):
    fam = FAMILY[s['id'].split('_')[1]]
    order = bool(s['order'])
    return {
        'id': s['id'], 'stratum': 'M', 'family': fam, 'generic_family': None, 'catalogue_row': s['row'],
        'files': [{'path': p, 'description': desc[p]} for p in s['files']],
        'task_text': s['text'],
        'allowed_task_words': list(s.get('allowed') or []),
        'invited_ids_author': list(s['invited']),
        'order_significant': order, 'sort_keys': list(s['keys']) if order else [],
        'dtype_significant': bool(s['dtype']),
        'intended_computation': s['intended'],
        'acceptable_variants': {'row_order': 'ties_only' if order else 'any', 'label_spelling': True,
                                'missing_value_representation': True, 'rounding_sig_digits': 6,
                                'notes': s.get('av_notes') or ''},
        'property_checks': s['checks'],
        'predicted_direction': {'direction': s['direction'], 'reason': s['reason']},
        'naive_path': 'naive.py', 'reference_path': 'reference.py',
        'so_question_id': None, 'so_url': None, 'so_creation_date': None, 'so_score': None, 'so_licence': None,
        'intent_summary': None, 'column_map': None,
        'invitation_strength': None, 'invited_ids_reviewer': None, 'fidelity': None, 'independent_card_ref': None,
        'blind_provenance': None,
        'drafted_by': 'pkg:TASKS_M2', 'status': DRAFT,
        'notes': s.get('notes') or ('Drafted %s by pkg:TASKS_M2 for catalogue row %s; naive.py shows the invited idiom, '
                                    'reference.py is the version-robust reference.' % (DATE, s['row'])),
    }


def header(s, kind):
    what = ('naive solution using the invited idiom of catalogue row %s' % s['row'] if kind == 'naive'
            else 'version-robust reference solution')
    return ('# %s: %s.\n# drafted_by pkg:TASKS_M2 (%s); status: %s.\n' % (s['id'], what, DATE, DRAFT))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*')
    a = ap.parse_args(argv)
    desc = descriptions()
    n = 0
    for s in load_specs():
        if a.only and s['id'] not in a.only:
            continue
        d = os.path.join(PKG, s['id'])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'task.json'), 'w', encoding='utf-8') as f:
            json.dump(task_json(s, desc), f, indent=1, ensure_ascii=False)
            f.write('\n')
        for kind, key in (('naive', 'naive'), ('reference', 'ref')):
            with open(os.path.join(d, kind + '.py'), 'w', encoding='utf-8') as f:
                f.write(header(s, kind) + s[key])
        n += 1
    print('built %d task folders under %s' % (n, PKG))


if __name__ == '__main__':
    main()
