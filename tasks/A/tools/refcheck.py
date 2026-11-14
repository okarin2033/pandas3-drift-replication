"""Reference check for stratum-A (or R) tasks (STAGE2 T4.5; FULL_PREREG section 10.1). pkg:TASKS_RA, 2026-11-11.

1. writes a jobs file (program_id ref/<task_id>, files from task.json, card = task.json);
2. runs harness/run_programs.py on E0a, E0b, E1, E2, E0pa, E3, E4 (F-main; at most 2 workers; --mem-limit-gb 2, machine rule);
3. compares the canonical result of every config with E0a using harness/oracle.compare with the task's card: each of E0pa,
   E1, E2, E3, E4 (and E0b, determinism) must be IDENTICAL or DTYPE_ONLY (ORDER_ONLY counts as a failure here);
4. evaluates the card's property checks on every config's canonical result (harness/harm_prelabel.check_properties).
Writes <pkg>/logs/refcheck.tsv and prints a summary. Usage: python3 -I -B tasks/A/tools/refcheck.py --pkg A [--only ID ...]
"""
import argparse, glob, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(S, 'harness'))
import oracle  # noqa: E402
import run_programs  # noqa: E402
from harm_prelabel import check_properties  # noqa: E402

CONFIGS = ['E0a', 'E0b', 'E1', 'E2', 'E0pa', 'E3', 'E4']
SIX = ['E0a', 'E0pa', 'E1', 'E2', 'E3', 'E4']
OK = {'IDENTICAL', 'DTYPE_ONLY'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pkg', required=True)
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--no-run', action='store_true')
    a = ap.parse_args()
    pdir = os.path.join(S, 'tasks', a.pkg)
    logs = os.path.join(pdir, 'logs')
    os.makedirs(logs, exist_ok=True)
    tasks = []
    for p in sorted(glob.glob(os.path.join(pdir, '*', 'task.json'))):
        t = json.load(open(p, encoding='utf-8'))
        if a.only and t['id'] not in a.only:
            continue
        tasks.append((t, p))
    jobs_path = os.path.join(logs, 'ref_jobs.jsonl')
    with open(jobs_path, 'w', encoding='utf-8') as f:
        for t, p in tasks:
            f.write(json.dumps({'program_id': 'ref/' + t['id'],
                                'program_path': os.path.relpath(os.path.join(os.path.dirname(p), 'reference.py'), S),
                                'task_id': t['id'], 'card': os.path.relpath(p, S),
                                'files': [x['path'] for x in t['files']]}) + '\n')
    out_root = os.path.join(logs, 'refruns')
    if not a.no_run:
        cmd = [sys.executable, '-I', '-B', os.path.join(S, 'harness', 'run_programs.py'), '--jobs', jobs_path,
               '--configs', ','.join(CONFIGS), '--out-root', out_root, '--workers', '2', '--mem-limit-gb', '2']
        r = subprocess.run(cmd, cwd=S, capture_output=True, text=True)
        open(os.path.join(logs, 'refruns_console.txt'), 'w', encoding='utf-8').write(r.stdout + r.stderr)
        print(r.stdout.strip().splitlines()[-3:] if r.stdout.strip() else r.stderr[-2000:])
    lines = ['task_id\tconfig\tstatus\tclass_vs_E0a\tproperty_failures\tmax_rss_mb']
    bad_tasks = {}
    for t, p in tasks:
        pid = 'ref/' + t['id']
        recs = {c: run_programs.load_record(out_root, c, pid) for c in CONFIGS}
        base = recs['E0a']
        for c in CONFIGS:
            r = recs[c]
            if r is None:
                lines.append('%s\t%s\tMISSING\t\t\t' % (t['id'], c))
                bad_tasks.setdefault(t['id'], []).append('%s missing' % c)
                continue
            cls = ''
            if c != 'E0a':
                if base is None or base.get('status') != 'ok':
                    cls = 'NO_BASE'
                else:
                    cls = oracle.compare(base, r, t)['class'] or 'NONE'
            pf = ''
            if r.get('status') == 'ok':
                fails = check_properties(r['result'], t['property_checks'], t)
                pf = ';'.join('%s:%s' % (x['check'], x['detail']) for x in fails)
            rss = (r.get('max_rss_bytes') or 0) / 1e6
            lines.append('%s\t%s\t%s\t%s\t%s\t%.0f' % (t['id'], c, r.get('status'), cls, pf, rss))
            if r.get('status') != 'ok':
                bad_tasks.setdefault(t['id'], []).append('%s status %s: %s' % (c, r.get('status'),
                                                                              (r.get('exc_msg') or '')[:200]))
            elif c != 'E0a' and cls not in OK:
                bad_tasks.setdefault(t['id'], []).append('%s class %s' % (c, cls))
            if pf and c in SIX + ['E0b']:
                bad_tasks.setdefault(t['id'], []).append('%s property %s' % (c, pf))
    with open(os.path.join(logs, 'refcheck.tsv'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    n_ok = len(tasks) - len(bad_tasks)
    print('references checked: %d; pass on all of %s (+E0b determinism) with property checks: %d; failing: %d'
          % (len(tasks), ','.join(SIX), n_ok, len(bad_tasks)))
    for k, v in sorted(bad_tasks.items()):
        print('  FAIL %s: %s' % (k, ' | '.join(v[:4])))
    return 0 if not bad_tasks else 1


if __name__ == '__main__':
    sys.exit(main())
