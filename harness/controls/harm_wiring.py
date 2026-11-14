# VERIFY (end-to-end wiring): harm_prelabel is called by analyze_full with real run records. Builds three scenarios from P+ programs
# (S01 -> expected HARM_3X, S03 -> FIX_3X, D01 -> NEITHER) with version-robust synthetic references and cards, runs them through
# run_programs and writes logs/controls/harm_wiring/{jobs,tasks}. Written 2026-11-11 by pkg:VERIFY. Standard library only.
# Run: python3 -I -B harness/controls/harm_wiring.py
import json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__)); S = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(S, 'logs', 'controls', 'harm_wiring')
SCEN = [('S01', 'HARM_3X', 'B01'), ('S03', 'FIX_3X', 'B02'), ('D01', 'NEITHER', 'B03')]
PROP = [{'check': 'no_null_text', 'args': {}}, {'check': 'no_all_missing_column', 'args': {}}]
def build():
    os.makedirs(os.path.join(OUT, 'generations', 'ctlharm'), exist_ok=True)
    os.makedirs(os.path.join(OUT, 'refs'), exist_ok=True)
    tasks, jobs, expect = [], [], {}
    for rid, exp, _ in SCEN:
        shutil.copyfile(os.path.join(S, 'mechanisms', 'confirm', rid + '.py'), os.path.join(OUT, 'generations', 'ctlharm', rid + '__s0.py'))
        shutil.copyfile(os.path.join(HERE, 'harm_wiring', rid + '_ref.py'), os.path.join(OUT, 'refs', rid + '_ref.py'))
        fam = {'S01': 'QF1_STRING', 'S03': 'QF1_STRING', 'D01': 'QF2_DATETIME'}[rid]
        tasks.append({'id': rid, 'stratum': 'M', 'family': fam, 'catalogue_row': rid, 'invited_ids_author': [rid],
                      'task_text': 'synthetic wiring task for %s' % rid, 'files': [{'path': 'x.csv', 'description': 'synthetic'}],
                      'order_significant': False, 'sort_keys': [], 'dtype_significant': False,
                      'acceptable_variants': {'row_order': 'any', 'label_spelling': True, 'missing_value_representation': True,
                                              'rounding_sig_digits': 6, 'notes': ''},
                      'property_checks': PROP})
        data = os.path.join('mechanisms', 'confirm', 'data', rid)
        jobs.append({'program_id': 'gen/ctlharm/%s__s0' % rid, 'program_path': 'logs/controls/harm_wiring/generations/ctlharm/%s__s0.py' % rid,
                     'task_id': rid, 'card': None, 'fixtures_root': data})
        jobs.append({'program_id': 'ref/%s' % rid, 'program_path': 'logs/controls/harm_wiring/refs/%s_ref.py' % rid,
                     'task_id': rid, 'card': None, 'fixtures_root': data})
        expect[rid] = exp
    json.dump({'schema_version': 'tasks/1', 'label': 'harm wiring, not study data', 'tasks': tasks}, open(os.path.join(OUT, 'tasks.json'), 'w'), indent=1)
    with open(os.path.join(OUT, 'jobs.jsonl'), 'w') as f:
        for j in jobs: f.write(json.dumps(j) + '\n')
    json.dump(expect, open(os.path.join(OUT, 'expect.json'), 'w'), indent=1)
    print('%d jobs' % len(jobs))



def evaluate():
    """python3 -I -B harness/controls/harm_wiring.py --eval > logs/controls/harm_wiring_eval_<date>.txt"""
    exp = json.load(open(os.path.join(OUT, 'expect.json')))
    bad = 0
    for ln in open(os.path.join(OUT, 'results', 'per_program.jsonl')):
        d = json.loads(ln)
        for pair in ('E0a~E1', 'E0a~E2'):
            got = d['targets'][pair]['harm_prelabel']
            ok = got == exp[d['task_id']]
            bad += not ok
            print('%s %s class %s primary_label %s harm_prelabel %s expected %s %s' % (d['task_id'], pair, d['targets'][pair]['class'],
                  d['targets'][pair]['primary_label'], got, exp[d['task_id']], 'OK' if ok else 'MISMATCH'))
    print('mismatches: %d' % bad)


if __name__ == '__main__':
    if '--eval' in sys.argv:
        evaluate()
    else:
        build()
