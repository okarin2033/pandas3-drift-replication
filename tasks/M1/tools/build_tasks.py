# Build tasks/M1/<id>/{task.json, naive.py, reference.py} from spec_qf1..4.py and write run job files.
# Written 2026-11-11 in package TASKS_M1. Standard library only; run with python3 -I -B from anywhere.
#   python3 -I -B tasks/M1/tools/build_tasks.py [--only ID,ID]
# Writes only under tasks/M1/. Existing task folders are overwritten (the builder is the single source of the drafts;
# every rewrite of a task text is logged by hand in tasks/M1/logs/REWRITES.md before re-running).
import argparse, csv, importlib.util, json, os, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
M1 = os.path.dirname(TOOLS)
STUDY = os.path.dirname(os.path.dirname(M1))
DRAFTED = 'pkg:TASKS_M1'
STATUS = 'prepared'
DATE = '2026-11-11'
GENERIC = [{'check': 'no_null_text', 'args': {}}, {'check': 'no_all_missing_column', 'args': {}}]


def load_specs():
    out = []
    for n in (1, 2, 3, 4):
        p = os.path.join(TOOLS, 'spec_qf%d.py' % n)
        spec = importlib.util.spec_from_file_location('spec_qf%d' % n, p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for t in mod.TASKS:
            t = dict(t)
            t['family'] = mod.FAMILY
            out.append(t)
    return out


def descriptions():
    with open(os.path.join(STUDY, 'fixtures', 'descriptions.tsv'), encoding='utf-8', newline='') as f:
        return {r['path']: r['description'] for r in csv.DictReader(f, delimiter='\t')}


def header(tid, kind):
    return ('# %s %s. drafted_by: %s; status: %s. Written %s.\n'
            % (tid, 'naive solution (invited idiom, section 4.4a)' if kind == 'naive' else 'reference solution (section 10.1)',
               DRAFTED, STATUS, DATE))


def task_json(t, desc):
    return {
        'id': t['id'], 'stratum': 'M', 'family': t['family'], 'generic_family': None, 'catalogue_row': t['row'],
        'files': [{'path': p, 'description': desc[p]} for p in t['files']],
        'task_text': t['text'], 'allowed_task_words': list(t['allowed']), 'invited_ids_author': list(t['invited']),
        'order_significant': bool(t['order']), 'sort_keys': list(t['keys']), 'dtype_significant': bool(t.get('dtype', False)),
        'intended_computation': t['intended'],
        'acceptable_variants': {'row_order': 'ties_only' if t['order'] else 'any', 'label_spelling': True,
                                'missing_value_representation': True, 'rounding_sig_digits': 6, 'notes': t['notes']},
        'property_checks': GENERIC + [{'check': c, 'args': a} for c, a in t['checks']],
        'predicted_direction': {'direction': t['direction'], 'reason': t['reason']},
        'naive_path': 'naive.py', 'reference_path': 'reference.py',
        'so_question_id': None, 'so_url': None, 'so_creation_date': None, 'so_score': None, 'so_licence': None,
        'intent_summary': None, 'column_map': None,
        'invitation_strength': None, 'invited_ids_reviewer': None, 'fidelity': None, 'independent_card_ref': None,
        'blind_provenance': None,
        'drafted_by': DRAFTED, 'status': STATUS,
        'notes': 'Drafted %s by %s (package TASKS_M1); task text, card, naive solution, reference and predicted direction '
                 'were prepared there.' % (DATE, DRAFTED),
    }


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    only = set(x for x in a.only.split(',') if x)
    desc = descriptions()
    specs = load_specs()
    ids = [t['id'] for t in specs]
    assert len(ids) == len(set(ids)), 'duplicate ids'
    naive_jobs, ref_jobs = [], []
    for t in specs:
        d = os.path.join(M1, t['id'])
        if not only or t['id'] in only:
            write(os.path.join(d, 'task.json'), json.dumps(task_json(t, desc), indent=1, ensure_ascii=False) + '\n')
            write(os.path.join(d, 'naive.py'), header(t['id'], 'naive') + t['naive'])
            write(os.path.join(d, 'reference.py'), header(t['id'], 'ref') + t['ref'])
        card = 'tasks/M1/%s/task.json' % t['id']
        naive_jobs.append({'program_id': 'naive/%s' % t['id'], 'program_path': 'tasks/M1/%s/naive.py' % t['id'],
                           'task_id': t['id'], 'card': card, 'files': t['files'], 'fixtures_root': None})
        ref_jobs.append({'program_id': 'ref/%s' % t['id'], 'program_path': 'tasks/M1/%s/reference.py' % t['id'],
                         'task_id': t['id'], 'card': card, 'files': t['files'], 'fixtures_root': None})
    for name, jobs in (('jobs_naive.jsonl', naive_jobs), ('jobs_ref.jsonl', ref_jobs)):
        write(os.path.join(M1, 'runs', name), ''.join(json.dumps(j, sort_keys=True) + '\n' for j in jobs))
    print('built %d task folders (%s); jobs: %d naive, %d ref' % (len(only) or len(specs), 'subset' if only else 'all',
                                                                 len(naive_jobs), len(ref_jobs)))


if __name__ == '__main__':
    main()
