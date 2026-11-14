# Check the reference solutions of tasks/M1 (FULL_PREREG 10.1, STAGE2 T4.5): canonical results IDENTICAL or DTYPE_ONLY across
# E0a, E0pa, E1, E2, E3, E4 (each compared with E0a, plus E0a~E0b determinism) under the task's card, and every property check
# of the card passes on all six results (harness/harm_prelabel.check_properties).
# Also records, for information only, which property checks the naive solution's E0a and E1 results fail.
# Written 2026-11-11 by pkg:TASKS_M1.
#   python3 -I -B tasks/M1/tools/check_refs.py -> tasks/M1/logs/ref_check.tsv (+ naive_properties.tsv) and a summary on stdout
import csv, json, os, sys

TOOLS = os.path.dirname(os.path.abspath(__file__))
M1 = os.path.dirname(TOOLS)
STUDY = os.path.dirname(os.path.dirname(M1))
sys.path.insert(0, os.path.join(STUDY, 'harness'))
import oracle  # noqa: E402
import run_programs  # noqa: E402
import harm_prelabel  # noqa: E402

SIX = ['E0a', 'E0pa', 'E1', 'E2', 'E3', 'E4']
OK = ('IDENTICAL', 'DTYPE_ONLY')


def main():
    tids = sorted(d for d in os.listdir(M1) if d.startswith('M_QF'))
    rows, prow, npass = [], [], 0
    for tid in tids:
        with open(os.path.join(M1, tid, 'task.json'), encoding='utf-8') as f:
            task = json.load(f)
        card = oracle.card_of(task)
        root = os.path.join(M1, 'runs', 'ref')
        recs = {c: run_programs.load_record(root, c, 'ref/' + tid) for c in SIX + ['E0b']}
        missing = [c for c, r in recs.items() if r is None or r.get('status') != 'ok']
        classes, failed_props = {}, {}
        if not missing:
            for c in ['E0b'] + SIX[1:]:
                classes[c] = oracle.compare(recs['E0a'], recs[c], card)['class']
            for c in SIX:
                try:
                    fl = harm_prelabel.check_properties(recs[c], task['property_checks'], task)
                except harm_prelabel.NotComparable as e:
                    fl = [{'check': 'NOT_COMPARABLE', 'detail': str(e)}]
                if fl:
                    failed_props[c] = fl
        ok = (not missing and all(v in OK for v in classes.values()) and classes.get('E0b') == 'IDENTICAL'
              and not failed_props)
        npass += ok
        rows.append({'task': tid, 'row': task['catalogue_row'], 'missing_or_not_ok': ','.join(missing) or '-',
                     **{'E0a~' + c: classes.get(c, '-') for c in ['E0b'] + SIX[1:]},
                     'property_failures': json.dumps(failed_props, ensure_ascii=False)[:300] if failed_props else '-',
                     'pass': 'PASS' if ok else 'FAIL'})
        # information: property checks on the naive results (not an acceptance item)
        nroot = os.path.join(M1, 'runs', 'naive')
        info = {'task': tid, 'direction': task['predicted_direction']['direction']}
        for c in ('E0a', 'E1'):
            r = run_programs.load_record(nroot, c, 'naive/' + tid)
            if r is None or r.get('status') != 'ok':
                info['naive_' + c] = 'not ok'
                continue
            try:
                fl = harm_prelabel.check_properties(r, task['property_checks'], task)
                info['naive_' + c] = ','.join(sorted(set(x['check'] for x in fl))) or 'all pass'
            except Exception as e:  # noqa: BLE001 (information only)
                info['naive_' + c] = 'error: %s' % type(e).__name__
        prow.append(info)
    for name, data in (('ref_check.tsv', rows), ('naive_properties.tsv', prow)):
        with open(os.path.join(M1, 'logs', name), 'w', encoding='utf-8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(data[0]), delimiter='\t', lineterminator='\n')
            w.writeheader()
            w.writerows(data)
    for r in rows:
        if r['pass'] != 'PASS':
            print('FAIL', r)
    print('references: %d/%d PASS (IDENTICAL/DTYPE_ONLY vs E0a on E0pa,E1,E2,E3,E4; E0b IDENTICAL; property checks pass on all six)'
          % (npass, len(rows)))
    return 0 if npass == len(rows) else 1


if __name__ == '__main__':
    sys.exit(main())
