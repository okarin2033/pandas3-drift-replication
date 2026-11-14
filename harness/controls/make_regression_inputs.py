# VERIFY (T6): build the regression inputs from the pilot (read-only) -> logs/regression/inputs/.
# Written 2026-11-11 by pkg:VERIFY. Standard library only. Run: python3 -I -B harness/controls/make_regression_inputs.py
# Copies the 3 pilot fixtures and the 480 main programs (t01-t48 x s0-s4 of qwen35_9b and sonnet55); never writes into the pilot.
# Pilot programs have no cards: tasks.json holds unflagged synthetic task entries (stratum 'A', pilot family as generic_family).
import hashlib, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
P = os.path.join(os.path.dirname(os.path.dirname(S)), 'pilots', 'r3')
OUT = os.path.join(S, 'logs', 'regression', 'inputs')
MODELS = ['qwen35_9b', 'sonnet55']


def main():
    tasks_pilot = json.load(open(os.path.join(P, 'data', 'tasks', 'tasks.json'), encoding='utf-8'))['tasks']
    os.makedirs(os.path.join(OUT, 'fixtures'), exist_ok=True)
    for fn in sorted(os.listdir(os.path.join(P, 'data', 'fixtures'))):
        if fn.endswith('.csv'):
            shutil.copyfile(os.path.join(P, 'data', 'fixtures', fn), os.path.join(OUT, 'fixtures', fn))
    tasks = []
    for t in tasks_pilot:
        tasks.append({'id': t['id'], 'stratum': 'A', 'family': None, 'generic_family': t['family'],
                      'order_significant': False, 'sort_keys': [], 'dtype_significant': False,
                      'note': 'PILOT REGRESSION, not study data; unflagged synthetic card (pilot programs have no cards)'})
    with open(os.path.join(OUT, 'tasks.json'), 'w', encoding='utf-8') as f:
        json.dump({'schema_version': 'tasks/1', 'label': 'pilot regression, not study data', 'tasks': tasks}, f, indent=1)
    jobs, n, manifest = [], 0, []
    for m in MODELS:
        d = os.path.join(OUT, 'generations', 'pilot_' + m)
        os.makedirs(d, exist_ok=True)
        for t in tasks_pilot:
            for k in range(5):
                fn = '%s__s%d.py' % (t['id'], k)
                src = os.path.join(P, 'data', 'generations', m, fn)
                dst = os.path.join(d, fn)
                shutil.copyfile(src, dst)
                n += 1
                manifest.append('%s  %s/%s' % (hashlib.sha256(open(dst, 'rb').read()).hexdigest(), 'pilot_' + m, fn))
                jobs.append({'program_id': 'gen/pilot_%s/%s__s%d' % (m, t['id'], k),
                             'program_path': 'logs/regression/inputs/generations/pilot_%s/%s' % (m, fn),
                             'task_id': t['id'], 'card': None, 'fixtures_root': 'logs/regression/inputs/fixtures'})
    with open(os.path.join(OUT, 'jobs.jsonl'), 'w', encoding='utf-8') as f:
        for j in jobs:
            f.write(json.dumps(j) + '\n')
    with open(os.path.join(OUT, 'INPUTS.sha256'), 'w') as f:
        f.write('\n'.join(manifest) + '\n')
    print('copied %d programs, %d fixtures, %d tasks' % (n, len(os.listdir(os.path.join(OUT, 'fixtures'))), len(tasks)))


if __name__ == '__main__':
    sys.exit(main())
