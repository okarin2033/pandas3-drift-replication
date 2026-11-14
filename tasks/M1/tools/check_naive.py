# Check the naive solutions of tasks/M1 (FULL_PREREG 4.4(a)): clean on 2.3.3 (E0a ok, E0a~E0b IDENTICAL) and value drift on a
# target where the task's catalogue row was confirmed (status.tsv drift_E1 / drift_E2 = yes).
# Written 2026-11-11 by pkg:TASKS_M1. Reads tasks/M1/runs/naive/compare/ (written by harness/run_programs.py --compare).
#   python3 -I -B tasks/M1/tools/check_naive.py  -> tasks/M1/logs/naive_check.tsv and a summary on stdout
import csv, json, os, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
M1 = os.path.dirname(TOOLS)
STUDY = os.path.dirname(os.path.dirname(M1))
CMP = os.path.join(M1, 'runs', 'naive', 'compare')


def load(pair, tid):
    p = os.path.join(CMP, pair, 'naive', tid + '.json')
    if not os.path.exists(p):
        return None
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def main():
    with open(os.path.join(STUDY, 'mechanisms', 'confirm', 'status.tsv'), encoding='utf-8', newline='') as f:
        status = {r['id']: r for r in csv.DictReader(f, delimiter='\t')}
    tids = sorted(d for d in os.listdir(M1) if d.startswith('M_QF'))
    rows, npass = [], 0
    for tid in tids:
        with open(os.path.join(M1, tid, 'task.json'), encoding='utf-8') as f:
            task = json.load(f)
        row = task['catalogue_row']
        st = status[row]
        targets = [c for c, k in (('E1', 'drift_E1'), ('E2', 'drift_E2')) if st[k] == 'yes']
        det = load('E0a~E0b', tid)
        res = {}
        for tg in ('E1', 'E2'):
            c = load('E0a~' + tg, tid)
            res[tg] = c
        clean = bool(det and det.get('clean_on_233'))
        drift_on = [tg for tg in targets if res[tg] and res[tg].get('drift')]
        ok = clean and bool(drift_on)
        npass += ok
        def fmt(c):
            if not c:
                return 'missing'
            return '%s/%s/%s' % (c.get('class'), c.get('magnitude'), 'silent' if c.get('silent') else 'warned' if c.get('drift') else '-')
        rows.append({'task': tid, 'row': row, 'confirmed_targets': ','.join(targets), 'clean_on_233': clean,
                     'det_class': det.get('class') if det else 'missing', 'E1': fmt(res['E1']), 'E2': fmt(res['E2']),
                     'drift_on_confirmed_target': ','.join(drift_on) or 'none', 'pass': 'PASS' if ok else 'FAIL',
                     'warned_E0a': (det or {}).get('warned_E0a', {}).get('prereg') if isinstance((det or {}).get('warned_E0a'), dict) else (det or {}).get('warned_E0a')})
    out = os.path.join(M1, 'logs', 'naive_check.tsv')
    with open(out, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t', lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        if r['pass'] != 'PASS':
            print('FAIL', r)
    print('naive: %d/%d PASS (clean on 2.3.3 and drift on a confirmed target); table %s' % (npass, len(rows), out))
    return 0 if npass == len(rows) else 1


if __name__ == '__main__':
    sys.exit(main())
