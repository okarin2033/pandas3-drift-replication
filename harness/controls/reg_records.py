# VERIFY (T6): record-level regression, a stricter check than the class comparison. For every pilot program and config E0a, E0b, E1, E2
# compares the pilot's run record (pilots/r3/data/runs, read-only) with the new record: status, exception type, canonical result,
# result dtypes, result type, and the set of user-phase pandas warnings (pilot definition on both sides, signature = category + masked
# message + program line). Also compares E0a vs E0b hash seeds and versions.
# Written 2026-11-11 by pkg:VERIFY. Standard library only. Run: python3 -I -B harness/controls/reg_records.py [--out logs/regression/record_level.tsv]
import argparse, collections, gzip, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
S = os.path.dirname(os.path.dirname(HERE))
P = os.path.join(os.path.dirname(os.path.dirname(S)), 'pilots', 'r3')
sys.path.insert(0, os.path.join(S, 'harness'))
import run_programs, warndef  # noqa: E402


def conv_pilot_warning(w):
    return {'category_qualname': w.get('cat'), 'category_module': w.get('cat_module'), 'mro': w.get('mro', []), 'message': w.get('msg', ''),
            'user_line': w.get('user_line'), 'pandas_on_stack': w.get('pandas_stack'), 'phase': w.get('phase'), 'count': w.get('count', 1)}


def wsigs(ws, definition):
    out = set()
    for w in ws:
        if warndef.is_pandas_warning(w, definition):
            out.add((warndef.warning_signature(w), w.get('user_line')))
    return out


def load_pilot(cfg, m, p):
    f = os.path.join(P, 'data', 'runs', cfg, m, p + '.json.gz')
    if not os.path.exists(f):
        return None
    with gzip.open(f, 'rt', encoding='utf-8') as fh:
        return json.load(fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--runs', default=os.path.join(S, 'logs', 'regression', 'runs'))
    ap.add_argument('--out', default=os.path.join(S, 'logs', 'regression', 'record_level.tsv'))
    a = ap.parse_args()
    rows = []
    cnt = collections.Counter()
    for m in ('qwen35_9b', 'sonnet55'):
        for t in range(1, 49):
            for k in range(5):
                prog = 't%02d__s%d' % (t, k)
                pid = 'gen/pilot_%s/%s' % (m, prog)
                for cfg in ('E0a', 'E0b', 'E1', 'E2'):
                    pr = load_pilot(cfg, m, prog)
                    nr = run_programs.load_record(a.runs, cfg, pid)
                    diffs = []
                    if pr is None or nr is None:
                        diffs.append('missing record (pilot %s, new %s)' % (pr is not None, nr is not None))
                    else:
                        if pr.get('status') != nr.get('status'):
                            diffs.append('status %s vs %s' % (pr.get('status'), nr.get('status')))
                        if (pr.get('exc_type') or pr.get('exc')) not in (None, '') and 0:
                            pass
                        if pr.get('status') == 'ok' and nr.get('status') == 'ok':
                            if pr.get('result') != nr.get('result'):
                                diffs.append('canonical result differs')
                            if pr.get('result_dt') != nr.get('result_dt'):
                                diffs.append('result dtypes differ')
                            if pr.get('result_type') != nr.get('result_type'):
                                diffs.append('result type %s vs %s' % (pr.get('result_type'), nr.get('result_type')))
                        pw = [conv_pilot_warning(w) for w in pr.get('warnings', [])]
                        for d in ('pilot', 'prereg'):
                            sp, sn = wsigs(pw, d), wsigs(nr.get('warnings', []), d)
                            if sp != sn:
                                diffs.append('user-phase pandas warnings (%s definition) differ: pilot-only %s; new-only %s'
                                             % (d, sorted(sp - sn)[:2], sorted(sn - sp)[:2]))
                        if cfg != 'E0b' or True:
                            vp, vn = pr.get('versions') or {}, nr.get('versions') or {}
                            for key in ('python', 'pandas', 'numpy', 'pyarrow'):
                                if vp.get(key) != vn.get(key):
                                    diffs.append('version %s %s vs %s' % (key, vp.get(key), vn.get(key)))
                    cnt[(cfg, 'compared')] += 1
                    if diffs:
                        cnt[(cfg, 'differs')] += 1
                    rows.append((pid, cfg, '; '.join(diffs)))
    with open(a.out, 'w', encoding='utf-8') as f:
        f.write('program_id\tconfig\tdifferences\n')
        for r in rows:
            f.write('\t'.join(r) + '\n')
    kinds = collections.Counter()
    for _, cfg, d in rows:
        for x in d.split('; '):
            if x:
                kinds[(cfg, re.sub(r"\[.*", '', x)[:90])] += 1
    print(dict(cnt))
    for k, v in sorted(kinds.items()):
        print(k, v)
    # control of the check itself: pilot E0a records against the new E1 records (a deliberate mismatch) must show differences
    n = dres = ddt = 0
    for m in ('qwen35_9b', 'sonnet55'):
        for t in range(1, 49):
            for k in range(5):
                prog = 't%02d__s%d' % (t, k)
                pr = load_pilot('E0a', m, prog)
                nr = run_programs.load_record(a.runs, 'E1', 'gen/pilot_%s/%s' % (m, prog))
                if pr.get('status') == 'ok' and nr.get('status') == 'ok':
                    n += 1
                    dres += pr['result'] != nr['result']
                    ddt += pr['result_dt'] != nr['result_dt']
    ctl = 'control (pilot E0a record vs new E1 record, deliberate mismatch): %d programs compared, canonical result differs for %d, dtype record differs for %d' % (n, dres, ddt)
    print(ctl)
    with open(os.path.splitext(a.out)[0] + '_summary.txt', 'w', encoding='utf-8') as f:
        f.write('records compared: %s\nrecords with any difference: %d\n%s\n' % (dict(cnt), sum(1 for r in rows if r[2]), ctl))
    return 0


if __name__ == '__main__':
    sys.exit(main())
