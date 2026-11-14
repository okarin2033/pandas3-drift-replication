# Run and check the naive and reference solutions of package TASKS_M2 with the study harness (harness/run_programs.py).
# Written 2026-11-11 by pkg:TASKS_M2. Standard library only (host side):
#   python3 -I -B tasks/M2/tools/check.py [--only ID ...] [--rerun] [--no-run]
# naive/<id>     runs on E0a, E0b, E1, E2 (F-main);  ref/<id> runs on E0a, E0b, E0pa, E1, E2, E3, E4 (F-main).
# Acceptance per task (STAGE2 T4.1, T4.5; FULL_PREREG 4.4(a), 10.1):
#   naive_ok = clean on 2.3.3 (E0a ok, E0a~E0b IDENTICAL) and drift (ORDER/DTYPE/VALUE_DRIFT or NO_RESULT, under the task card) on
#              E0a~E1 or E0a~E2 where the catalogue row was confirmed (status.tsv drift_E1 / drift_E2 = yes);
#   ref_ok   = every run ok, E0a~E0b IDENTICAL, and E0a vs each of E0pa, E1, E2, E3, E4 IDENTICAL or DTYPE_ONLY under the task card,
#              and the property checks of the card pass on all six configs.
# Also recorded (information for the predicted direction, not an acceptance item): harm_prelabel(naive E0a, naive target,
# reference E0a, card) for the confirmed target(s).
# Writes tasks/M2/logs/check_results.json and tasks/M2/logs/check_results.tsv.
import argparse, csv, json, os, subprocess, sys, time

TOOLS = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(TOOLS)
STUDY = os.path.dirname(os.path.dirname(PKG))
HARNESS = os.path.join(STUDY, 'harness')
sys.path.insert(0, HARNESS)
import oracle
import run_programs as rp
import harm_prelabel as hp

RUNS = os.path.join(PKG, 'runs')
LOGS = os.path.join(PKG, 'logs')
WORK = os.environ.get('M2_WORK') or os.path.join(os.environ.get('TMPDIR', '/tmp'), 'm2_work')
NAIVE_CFG = ['E0a', 'E0b', 'E1', 'E2']
REF_CFG = ['E0a', 'E0b', 'E0pa', 'E1', 'E2', 'E3', 'E4']
OK_REF = ('IDENTICAL', 'DTYPE_ONLY')


def tasks(only=None):
    out = []
    for name in sorted(os.listdir(PKG)):
        p = os.path.join(PKG, name, 'task.json')
        if name.startswith('M_QF') and os.path.isfile(p) and (not only or name in only):
            with open(p, encoding='utf-8') as f:
                out.append(json.load(f))
    return out


def confirmed_targets():
    with open(os.path.join(STUDY, 'mechanisms', 'confirm', 'status.tsv'), encoding='utf-8', newline='') as f:
        return {r['id']: [t for t, c in (('E1', r['drift_E1']), ('E2', r['drift_E2'])) if c == 'yes']
                for r in csv.DictReader(f, delimiter='\t')}


def write_jobs(ts, kind, path):
    with open(path, 'w', encoding='utf-8') as f:
        for t in ts:
            tid = t['id']
            f.write(json.dumps({'program_id': '%s/%s' % (kind, tid),
                                'program_path': 'tasks/M2/%s/%s.py' % (tid, 'naive' if kind == 'naive' else 'reference'),
                                'task_id': tid, 'card': 'tasks/M2/%s/task.json' % tid,
                                'files': [x['path'] for x in t['files']], 'fixtures_root': None}) + '\n')


def run(jobs, cfgs, rerun):
    cmd = [sys.executable, '-I', '-B', os.path.join(HARNESS, 'run_programs.py'), '--jobs', jobs, '--configs', ','.join(cfgs),
           '--out-root', RUNS, '--work', WORK, '--workers', '2', '--mem-limit-gb', '2', '--compare']
    if rerun:
        cmd.append('--force')
    print('$', ' '.join(cmd[3:]), flush=True)
    r = subprocess.run(cmd, cwd=STUDY)
    if r.returncode != 0:
        print('run_programs exit code', r.returncode)


def recs(pid, cfgs):
    return {c: rp.load_record(RUNS, c, pid) for c in cfgs}


def evaluate(t, targets):
    tid = t['id']
    card = oracle.card_of(t)
    row = t['catalogue_row']
    out = {'id': tid, 'row': row, 'order_significant': t['order_significant'], 'dtype_significant': t['dtype_significant'],
           'predicted': t['predicted_direction']['direction'], 'targets_confirmed': targets.get(row, [])}
    # ---- naive
    nr = recs('naive/' + tid, NAIVE_CFG)
    a, b = nr['E0a'], nr['E0b']
    clean = bool(a and a.get('status') == 'ok' and b and b.get('status') == 'ok'
                 and oracle.compare(a, b, None)['class'] == 'IDENTICAL')
    out['naive_status'] = {c: (r or {}).get('status') for c, r in nr.items()}
    out['naive_clean_233'] = clean
    out['naive_warned_E0a'] = bool(a and any(w.get('phase') == 'user' for w in a.get('warnings') or []))
    drift_on = []
    for tg in ('E1', 'E2'):
        r = nr[tg]
        if a is None or r is None or a.get('status') != 'ok':
            out['naive_%s' % tg] = None
            continue
        c = oracle.compare(a, r, card)
        blk = oracle.pair_block(a, r, card)
        out['naive_%s' % tg] = {'class': c['class'], 'drift': c['drift'], 'magnitude': c.get('magnitude'),
                                'silent': blk.get('silent'), 'class_pilot_rule': c.get('class_pilot_rule')}
        if c['drift'] and tg in out['targets_confirmed']:
            drift_on.append(tg)
    out['naive_drift_on_confirmed'] = drift_on
    out['naive_ok'] = clean and bool(drift_on)
    # ---- reference
    rr = recs('ref/' + tid, REF_CFG)
    out['ref_status'] = {c: (r or {}).get('status') for c, r in rr.items()}
    ref_ok = all(r is not None and r.get('status') == 'ok' for r in rr.values())
    cls = {}
    if ref_ok:
        cls['E0a~E0b'] = oracle.compare(rr['E0a'], rr['E0b'], None)['class']
        ref_ok = cls['E0a~E0b'] == 'IDENTICAL'
        for c in ('E0pa', 'E1', 'E2', 'E3', 'E4'):
            cls['E0a~' + c] = oracle.compare(rr['E0a'], rr[c], card)['class']
            ref_ok = ref_ok and cls['E0a~' + c] in OK_REF
    out['ref_classes'] = cls
    fails = {}
    for c in ('E0a', 'E0pa', 'E1', 'E2', 'E3', 'E4'):
        r = rr[c]
        if r is not None and r.get('status') == 'ok':
            try:
                f = hp.check_properties(r, t['property_checks'], t)
            except Exception as e:      # NotComparable etc.
                f = [{'check': 'evaluator', 'detail': '%s: %s' % (type(e).__name__, e)}]
            if f:
                fails[c] = f
    out['ref_property_failures'] = fails
    out['ref_ok'] = ref_ok and not fails
    # ---- pre-label of the naive pair (information for predicted_direction)
    pl = {}
    for tg in out['targets_confirmed']:
        if a is not None and nr[tg] is not None and rr['E0a'] is not None:
            try:
                pl[tg] = hp.harm_prelabel(a, nr[tg], rr['E0a'], t)['label']
            except Exception as e:
                pl[tg] = 'ERROR %s' % type(e).__name__
    out['naive_prelabel'] = pl
    exp = {'HARM': 'HARM_3X', 'FIX': 'FIX_3X', 'BOTH': 'BOTH_ACCEPTABLE'}[out['predicted']]
    out['prelabel_matches_prediction'] = bool(pl) and all(v == exp for v in pl.values())
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--prefix', help='select task ids starting with this text, e.g. M_QF6')
    ap.add_argument('--rerun', action='store_true', help='force re-running the selected programs')
    ap.add_argument('--no-run', action='store_true')
    a = ap.parse_args(argv)
    if a.prefix:
        a.only = [n for n in sorted(os.listdir(PKG)) if n.startswith(a.prefix)]
    ts = tasks(a.only)
    os.makedirs(LOGS, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    if not a.no_run:
        jn, jr = os.path.join(WORK, 'jobs_naive.jsonl'), os.path.join(WORK, 'jobs_ref.jsonl')
        write_jobs(ts, 'naive', jn)
        write_jobs(ts, 'ref', jr)
        run(jn, NAIVE_CFG, a.rerun)
        run(jr, REF_CFG, a.rerun)
    targets = confirmed_targets()
    res_path = os.path.join(LOGS, 'check_results.json')
    old = {}
    if os.path.exists(res_path):
        with open(res_path, encoding='utf-8') as f:
            old = {r['id']: r for r in json.load(f)['tasks']}
    for t in ts:
        old[t['id']] = evaluate(t, targets)
    allt = [old[k] for k in sorted(old) if os.path.isfile(os.path.join(PKG, k, 'task.json'))]
    with open(res_path, 'w', encoding='utf-8') as f:
        json.dump({'written': time.strftime('%Y-%m-%d %H:%M %Z'), 'tasks': allt}, f, indent=1, default=str)
    cols = ['id', 'row', 'predicted', 'naive_ok', 'naive_E1', 'naive_E2', 'ref_ok', 'prelabel', 'prelabel_ok', 'silent_E1']
    with open(os.path.join(LOGS, 'check_results.tsv'), 'w', encoding='utf-8') as f:
        f.write('\t'.join(cols) + '\n')
        for r in allt:
            e1, e2 = r.get('naive_E1') or {}, r.get('naive_E2') or {}
            f.write('\t'.join(str(x) for x in [r['id'], r['row'], r['predicted'], r['naive_ok'], e1.get('class'), e2.get('class'),
                                                r['ref_ok'], ','.join('%s:%s' % kv for kv in r['naive_prelabel'].items()),
                                                r['prelabel_matches_prediction'], e1.get('silent')]) + '\n')
    for r in allt:
        if a.only and r['id'] not in a.only:
            continue
        e1, e2 = r.get('naive_E1') or {}, r.get('naive_E2') or {}
        print('%-9s %s naive_ok=%-5s E1=%-12s E2=%-12s ref_ok=%-5s pl=%s pred=%s%s' % (
            r['id'], r['row'], r['naive_ok'], e1.get('class'), e2.get('class'), r['ref_ok'],
            ','.join('%s:%s' % kv for kv in r['naive_prelabel'].items()), r['predicted'],
            '' if r['ref_ok'] else ' REF:%s %s %s' % (r['ref_status'], r['ref_classes'],
                                                       json.dumps(r['ref_property_failures'])[:300])))
    n = len(allt)
    print('tasks %d  naive_ok %d  ref_ok %d  prelabel=prediction %d' % (
        n, sum(r['naive_ok'] for r in allt), sum(r['ref_ok'] for r in allt), sum(r['prelabel_matches_prediction'] for r in allt)))


if __name__ == '__main__':
    main()
