# VERIFY (T5.11, P-): job, task and generation files for the negative controls (harness/controls/controls.json).
# Written 2026-11-11 by pkg:VERIFY. Standard library only. Run after make_pminus.py: python3 -I -B harness/controls/pminus_build.py
# Layout under logs/controls/pminus/: generations/ctlminus/<name>__s0.py, tasks.json (synthetic cards), jobs.jsonl.
import json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(S, 'logs', 'controls', 'pminus')


def main():
    ctl = json.load(open(os.path.join(HERE, 'controls.json'), encoding='utf-8'))['controls']
    os.makedirs(os.path.join(OUT, 'generations', 'ctlminus'), exist_ok=True)
    tasks, jobs = [], []
    for c in ctl:
        n = c['name']
        shutil.copyfile(os.path.join(HERE, 'programs', n + '.py'), os.path.join(OUT, 'generations', 'ctlminus', n + '__s0.py'))
        card = c['card']
        tasks.append({'id': n, 'stratum': 'A', 'family': None, 'generic_family': None,
                      'order_significant': bool(card.get('order_significant')), 'sort_keys': card.get('sort_keys') or [],
                      'dtype_significant': bool(card.get('dtype_significant')), 'note': 'oracle control, not study data'})
        jobs.append({'program_id': 'gen/ctlminus/%s__s0' % n,
                     'program_path': 'logs/controls/pminus/generations/ctlminus/%s__s0.py' % n,
                     'task_id': n, 'card': ({'order_significant': bool(card.get('order_significant')), 'sort_keys': card.get('sort_keys') or [],
                                             'dtype_significant': bool(card.get('dtype_significant'))} if card else None),
                     'fixtures_root': 'harness/controls/data'})
    with open(os.path.join(OUT, 'tasks.json'), 'w', encoding='utf-8') as f:
        json.dump({'schema_version': 'tasks/1', 'label': 'oracle controls, not study data', 'tasks': tasks}, f, indent=1)
    with open(os.path.join(OUT, 'jobs.jsonl'), 'w', encoding='utf-8') as f:
        for j in jobs:
            f.write(json.dumps(j) + '\n')
    print('%d controls' % len(jobs))


if __name__ == '__main__':
    sys.exit(main())
